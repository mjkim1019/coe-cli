"""
Base Coder - 모든 편집 전략의 기본 클래스
Aider에서 영감을 받은 구조화된 편집 시스템
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import os
import json
from pathlib import Path

from actions.file_editor import FileEditor, EditOperation
from cli.core.base_prompts import BasePrompts

class BaseCoder(ABC):
    """모든 편집 전략의 기본 클래스"""
    
    def __init__(self, file_editor: FileEditor):
        self.file_editor = file_editor
        self.strategy_name = self.__class__.__name__.replace('Coder', '').lower()
        self.prompts = self.get_prompts_class()
        
    @abstractmethod
    def get_prompts_class(self) -> BasePrompts:
        """각 전략에 맞는 프롬프트 클래스를 반환"""
        pass
    
    @abstractmethod
    def parse_response(self, response: str, context_files: Dict[str, str]) -> Dict[str, str]:
        """AI 응답을 파싱해서 파일별 내용 추출"""
        pass
    
    @abstractmethod
    def validate_response(self, parsed_files: Dict[str, str]) -> Tuple[bool, str]:
        """파싱된 응답의 유효성 검증"""
        pass
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """전략에 대한 정보 반환"""
        return {
            'name': self.strategy_name,
            'description': self.__doc__ or "편집 전략",
            'supports_partial_edit': self.supports_partial_edit(),
            'supports_multiple_files': self.supports_multiple_files(),
            'best_for': self.get_best_use_cases()
        }
    
    @abstractmethod
    def supports_partial_edit(self) -> bool:
        """부분 편집을 지원하는지 여부"""
        pass
    
    @abstractmethod
    def supports_multiple_files(self) -> bool:
        """다중 파일 편집을 지원하는지 여부"""
        pass
    
    @abstractmethod
    def get_best_use_cases(self) -> List[str]:
        """이 전략이 가장 적합한 사용 사례들"""
        pass
    
    def preview_changes(self, response: str, context_files: Dict[str, str]) -> Dict[str, Dict[str, Any]]:
        """변경사항 미리보기 생성"""
        try:
            parsed_files = self.parse_response(response, context_files)
            is_valid, error_msg = self.validate_response(parsed_files)
            
            if not is_valid:
                return {
                    'error': {
                        'message': error_msg,
                        'strategy': self.strategy_name
                    }
                }
            
            return self.file_editor.preview_changes_from_dict(parsed_files)
        
        except Exception as e:
            return {
                'error': {
                    'message': f"미리보기 생성 중 오류: {str(e)}",
                    'strategy': self.strategy_name
                }
            }
    
    def apply_changes(self, response: str, context_files: Dict[str, str], description: str = "") -> EditOperation:
        """변경사항을 실제 파일에 적용"""
        parsed_files = self.parse_response(response, context_files)
        is_valid, error_msg = self.validate_response(parsed_files)
        
        if not is_valid:
            raise ValueError(f"{self.strategy_name} 전략 오류: {error_msg}")
        
        # 설명에 전략 정보 추가
        full_description = f"[{self.strategy_name}] {description or '사용자 요청으로 적용'}"
        
        return self.file_editor.apply_changes_from_dict(parsed_files, full_description)
    
    def get_system_prompt(self, context_files: Dict[str, str]) -> str:
        """시스템 프롬프트 생성 (컨텍스트 파일 정보 포함)"""
        base_prompt = self.prompts.main_system
        
        if context_files:
            file_info = f"""

현재 작업 중인 파일들:
{chr(10).join([f"- {path}" for path in context_files.keys()])}

이 파일들의 내용을 참고하여 요청된 변경사항을 적용하세요.
"""
            base_prompt += file_info
        
        return base_prompt
    
    def format_context_for_ai(self, context_files: Dict[str, str], user_request: str) -> str:
        """AI에게 전달할 컨텍스트 포맷팅"""
        formatted = f"편집 요청: {user_request}\n\n"

        if context_files:
            formatted += "작업 파일들:\n\n"
            for file_path, content in context_files.items():
                formatted += f"파일: {file_path}\n```\n{content}\n```\n\n"

        return formatted

    def get_repo_map(self,
                     chat_files: Optional[List[str]] = None,
                     other_files: Optional[List[str]] = None,
                     mentioned_fnames: Optional[List[str]] = None,
                     mentioned_idents: Optional[List[str]] = None,
                     force_refresh: bool = False) -> Optional[str]:
        """레포지토리 맵 생성 - 코드베이스의 구조적 개요 제공"""
        from .repo_mapper import RepoMapper

        # RepoMapper 인스턴스 생성 (캐싱 지원)
        if not hasattr(self, '_repo_mapper') or force_refresh:
            self._repo_mapper = RepoMapper()

        # 레포맵 생성
        return self._repo_mapper.generate_map(
            chat_files=chat_files,
            other_files=other_files,
            mentioned_fnames=mentioned_fnames,
            mentioned_idents=mentioned_idents,
            force_refresh=force_refresh
        )

class CoderRegistry:
    """사용 가능한 모든 코더를 관리하는 레지스트리"""
    
    def __init__(self):
        self._coders: Dict[str, type] = {}
        self._instances: Dict[str, BaseCoder] = {}
    
    def register(self, name: str, coder_class: type):
        """코더 클래스 등록"""
        self._coders[name] = coder_class
    
    def get_coder(self, name: str, file_editor: FileEditor) -> BaseCoder:
        """코더 인스턴스 반환 (싱글톤)"""
        if name not in self._instances:
            if name not in self._coders:
                raise ValueError(f"Unknown coder: {name}")
            self._instances[name] = self._coders[name](file_editor)
        return self._instances[name]
    
    def list_coders(self) -> Dict[str, Dict[str, Any]]:
        """사용 가능한 모든 코더 정보 반환"""
        result = {}
        dummy_editor = FileEditor()  # 임시 에디터
        
        for name, coder_class in self._coders.items():
            try:
                instance = coder_class(dummy_editor)
                result[name] = instance.get_strategy_info()
            except Exception as e:
                result[name] = {'error': str(e)}
        
        return result

# 전역 레지스트리 인스턴스
registry = CoderRegistry()