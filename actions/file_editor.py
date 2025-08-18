"""
파일 수정 시스템 - Aider에서 영감을 받은 백업/되돌리기 기능 포함
"""
import os
import json
import shutil
import difflib
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import re

@dataclass
class FileChange:
    """파일 변경사항을 나타내는 데이터 클래스"""
    file_path: str
    original_content: str
    new_content: str
    timestamp: str
    change_id: str
    backup_path: str
    
    def to_dict(self):
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data):
        return cls(**data)

@dataclass
class EditOperation:
    """편집 작업을 나타내는 데이터 클래스"""
    operation_id: str
    timestamp: str
    changes: List[FileChange]
    description: str
    
    def to_dict(self):
        return {
            'operation_id': self.operation_id,
            'timestamp': self.timestamp,
            'changes': [change.to_dict() for change in self.changes],
            'description': self.description
        }
    
    @classmethod
    def from_dict(cls, data):
        changes = [FileChange.from_dict(change) for change in data['changes']]
        return cls(
            operation_id=data['operation_id'],
            timestamp=data['timestamp'],
            changes=changes,
            description=data['description']
        )

class FileEditor:
    """파일 편집 및 버전 관리 시스템"""
    
    def __init__(self, backup_dir: str = ".swing_backups"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
        
        # 히스토리 파일
        self.history_file = self.backup_dir / "edit_history.json"
        self.operations = self._load_history()
        
    def _load_history(self) -> List[EditOperation]:
        """편집 히스토리를 로드"""
        if not self.history_file.exists():
            return []
        
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [EditOperation.from_dict(op) for op in data]
        except Exception as e:
            print(f"히스토리 로드 실패: {e}")
            return []
    
    def _save_history(self):
        """편집 히스토리를 저장"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump([op.to_dict() for op in self.operations], f, 
                         ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"히스토리 저장 실패: {e}")
    
    def _generate_change_id(self) -> str:
        """고유한 변경 ID 생성"""
        timestamp = datetime.now().isoformat()
        return hashlib.md5(timestamp.encode()).hexdigest()[:8]
    
    def _create_backup(self, file_path: str, content: str) -> str:
        """파일 백업 생성"""
        change_id = self._generate_change_id()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 백업 파일명 생성
        file_name = os.path.basename(file_path)
        backup_name = f"{timestamp}_{change_id}_{file_name}"
        backup_path = self.backup_dir / backup_name
        
        # 백업 저장
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return str(backup_path)
    
    def parse_edit_response(self, response: str) -> Dict[str, str]:
        """EditPrompts 응답을 파싱해서 파일별 내용 추출"""
        files = {}
        
        # 더 정확한 파일 패턴 매칭
        # 1. 파일 경로 (확장자 포함, 경로 구분자 포함)
        # 2. 코드 블록 (언어 지정 가능)
        patterns = [
            # 표준 형식: path/file.ext\n```lang\ncontent\n```
            r'^([^\s\n`]+\.[a-zA-Z0-9]+)\s*\n```[a-zA-Z0-9]*\s*\n(.*?)\n```',
            # 확장자 없는 파일: path/filename\n```lang\ncontent\n```
            r'^([^\s\n`]+/[^\s\n`./]+)\s*\n```[a-zA-Z0-9]*\s*\n(.*?)\n```',
            # 단순 파일명: filename.ext\n```lang\ncontent\n```
            r'^([a-zA-Z0-9_.-]+\.[a-zA-Z0-9]+)\s*\n```[a-zA-Z0-9]*\s*\n(.*?)\n```'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, response, re.MULTILINE | re.DOTALL)
            for file_path, content in matches:
                # 파일 경로 정리
                file_path = file_path.strip()
                content = content.strip()
                
                if file_path and content:
                    files[file_path] = content
        
        # 디버깅을 위한 로깅
        if not files:
            print(f"[DEBUG] 파싱 실패. 응답 내용 미리보기:")
            preview = response[:500] + ("..." if len(response) > 500 else "")
            print(f"[DEBUG] '{preview}'")
            
            # 간단한 패턴도 시도
            simple_pattern = r'```[a-zA-Z0-9]*\s*\n(.*?)\n```'
            simple_matches = re.findall(simple_pattern, response, re.DOTALL)
            if simple_matches:
                # 첫 번째 코드 블록을 임시 파일로 사용
                print("[DEBUG] 간단한 패턴으로 코드 블록 발견, temp.py로 저장")
                files['temp.py'] = simple_matches[0].strip()
        
        return files
    
    def generate_diff(self, file_path: str, original: str, new: str) -> str:
        """두 파일 버전 간의 diff 생성"""
        diff_lines = list(difflib.unified_diff(
            original.splitlines(keepends=True),
            new.splitlines(keepends=True),
            fromfile=f"{file_path} (original)",
            tofile=f"{file_path} (modified)",
            lineterm=""
        ))
        
        return ''.join(diff_lines)
    
    def generate_visual_diff(self, file_path: str, original: str, new: str) -> List[Tuple[str, str]]:
        """시각적 diff 생성 (Rich 스타일링을 위한 튜플 리스트 반환)"""
        diff_lines = list(difflib.unified_diff(
            original.splitlines(keepends=True),
            new.splitlines(keepends=True),
            fromfile=f"{file_path} (original)",
            tofile=f"{file_path} (modified)",
            lineterm="",
            n=3  # 컨텍스트 라인 수
        ))
        
        visual_diff = []
        
        for line in diff_lines:
            line = line.rstrip('\n')
            
            if line.startswith('---') or line.startswith('+++'):
                # 파일 헤더
                visual_diff.append(('header', line))
            elif line.startswith('@@'):
                # 라인 번호 정보
                visual_diff.append(('hunk', line))
            elif line.startswith('-'):
                # 삭제된 라인
                visual_diff.append(('removed', line))
            elif line.startswith('+'):
                # 추가된 라인
                visual_diff.append(('added', line))
            elif line.startswith(' '):
                # 컨텍스트 라인
                visual_diff.append(('context', line))
            else:
                # 기타
                visual_diff.append(('neutral', line))
        
        return visual_diff
    
    def preview_changes(self, edit_response: str) -> Dict[str, Dict[str, Any]]:
        """변경사항 미리보기 생성"""
        files_to_change = self.parse_edit_response(edit_response)
        preview = {}
        
        for file_path, new_content in files_to_change.items():
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    original_content = f.read()
            else:
                original_content = ""
            
            diff = self.generate_diff(file_path, original_content, new_content)
            visual_diff = self.generate_visual_diff(file_path, original_content, new_content)
            
            preview[file_path] = {
                'original': original_content,
                'new': new_content,
                'diff': diff,
                'visual_diff': visual_diff,
                'exists': os.path.exists(file_path)
            }
        
        return preview
    
    def preview_changes_from_dict(self, files_dict: Dict[str, str]) -> Dict[str, Dict[str, Any]]:
        """딕셔너리로부터 변경사항 미리보기 생성"""
        preview = {}
        
        for file_path, new_content in files_dict.items():
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    original_content = f.read()
            else:
                original_content = ""
            
            diff = self.generate_diff(file_path, original_content, new_content)
            visual_diff = self.generate_visual_diff(file_path, original_content, new_content)
            
            preview[file_path] = {
                'original': original_content,
                'new': new_content,
                'diff': diff,
                'visual_diff': visual_diff,
                'exists': os.path.exists(file_path)
            }
        
        return preview
    
    def apply_changes_from_dict(self, files_dict: Dict[str, str], description: str = "") -> EditOperation:
        """딕셔너리로부터 변경사항을 실제 파일에 적용"""
        changes = []
        operation_id = self._generate_change_id()
        timestamp = datetime.now().isoformat()
        
        # 각 파일에 대해 변경사항 적용
        for file_path, new_content in files_dict.items():
            # 기존 내용 읽기
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    original_content = f.read()
            else:
                original_content = ""
                # 디렉토리 생성
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # 백업 생성
            backup_path = self._create_backup(file_path, original_content)
            
            # 파일 변경사항 기록
            change = FileChange(
                file_path=file_path,
                original_content=original_content,
                new_content=new_content,
                timestamp=timestamp,
                change_id=self._generate_change_id(),
                backup_path=backup_path
            )
            changes.append(change)
            
            # 새 내용으로 파일 쓰기
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
        
        # 편집 작업 기록
        operation = EditOperation(
            operation_id=operation_id,
            timestamp=timestamp,
            changes=changes,
            description=description or f"{len(changes)}개 파일 수정"
        )
        
        self.operations.append(operation)
        self._save_history()
        
        return operation
    
    def apply_changes(self, edit_response: str, description: str = "") -> EditOperation:
        """변경사항을 실제 파일에 적용"""
        files_to_change = self.parse_edit_response(edit_response)
        changes = []
        operation_id = self._generate_change_id()
        timestamp = datetime.now().isoformat()
        
        # 각 파일에 대해 변경사항 적용
        for file_path, new_content in files_to_change.items():
            # 기존 내용 읽기
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    original_content = f.read()
            else:
                original_content = ""
                # 디렉토리 생성
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # 백업 생성
            backup_path = self._create_backup(file_path, original_content)
            
            # 파일 변경사항 기록
            change = FileChange(
                file_path=file_path,
                original_content=original_content,
                new_content=new_content,
                timestamp=timestamp,
                change_id=self._generate_change_id(),
                backup_path=backup_path
            )
            changes.append(change)
            
            # 새 내용으로 파일 쓰기
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
        
        # 편집 작업 기록
        operation = EditOperation(
            operation_id=operation_id,
            timestamp=timestamp,
            changes=changes,
            description=description or f"{len(changes)}개 파일 수정"
        )
        
        self.operations.append(operation)
        self._save_history()
        
        return operation
    
    def rollback_operation(self, operation_id: str) -> bool:
        """특정 편집 작업을 롤백"""
        # 해당 작업 찾기
        operation = None
        for op in self.operations:
            if op.operation_id == operation_id:
                operation = op
                break
        
        if not operation:
            return False
        
        # 각 변경사항을 원래대로 되돌리기
        for change in operation.changes:
            try:
                with open(change.file_path, 'w', encoding='utf-8') as f:
                    f.write(change.original_content)
            except Exception as e:
                print(f"롤백 실패 ({change.file_path}): {e}")
                return False
        
        return True
    
    def get_history(self, limit: int = 10) -> List[EditOperation]:
        """편집 히스토리 반환 (최신순)"""
        return sorted(self.operations, key=lambda x: x.timestamp, reverse=True)[:limit]
    
    def cleanup_backups(self, days: int = 7):
        """오래된 백업 파일 정리"""
        cutoff_date = datetime.now().timestamp() - (days * 24 * 60 * 60)
        
        for backup_file in self.backup_dir.glob("*"):
            if backup_file.is_file() and backup_file.name != "edit_history.json":
                if backup_file.stat().st_mtime < cutoff_date:
                    try:
                        backup_file.unlink()
                    except Exception as e:
                        print(f"백업 파일 삭제 실패: {e}")