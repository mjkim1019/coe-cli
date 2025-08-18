"""
WholeFile Coder - 전체 파일을 완전히 교체하는 편집 전략
작은 파일이나 대규모 변경에 최적화됨
"""
import re
from typing import Dict, List, Tuple
from .base_coder import BaseCoder, registry
from .wholefile_prompts import WholeFilePrompts

class WholeFileCoder(BaseCoder):
    """전체 파일 교체 전략 - 파일 전체를 새로운 내용으로 대체"""
    
    def get_prompts_class(self) -> WholeFilePrompts:
        return WholeFilePrompts()
    
    def parse_response(self, response: str, context_files: Dict[str, str]) -> Dict[str, str]:
        """AI 응답에서 파일별 완전한 내용 추출"""
        files = {}
        
        # WholeFile 전략용 패턴들 (더 엄격한 매칭)
        patterns = [
            # 표준 형식: path/file.ext\n```lang\ncontent\n```
            r'^([^\s\n`]+\.[a-zA-Z0-9]+)\s*\n```[a-zA-Z0-9]*\s*\n(.*?)\n```',
            # 상대 경로: ./path/file.ext\n```lang\ncontent\n```
            r'^(\./[^\s\n`]+\.[a-zA-Z0-9]+)\s*\n```[a-zA-Z0-9]*\s*\n(.*?)\n```',
            # 단순 파일명: filename.ext\n```lang\ncontent\n```
            r'^([a-zA-Z0-9_.-]+\.[a-zA-Z0-9]+)\s*\n```[a-zA-Z0-9]*\s*\n(.*?)\n```'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, response, re.MULTILINE | re.DOTALL)
            for file_path, content in matches:
                file_path = file_path.strip()
                content = content.strip()
                
                # 내용이 너무 짧으면 의심 (완전한 파일이 아닐 가능성)
                if file_path and content and len(content) > 10:
                    files[file_path] = content
        
        # 디버깅 정보 출력
        if not files:
            print(f"[WholeFile DEBUG] 파싱 실패. 응답 미리보기:")
            preview = response[:300] + ("..." if len(response) > 300 else "")
            print(f"[WholeFile DEBUG] '{preview}'")
        else:
            print(f"[WholeFile DEBUG] {len(files)}개 파일 파싱 성공: {list(files.keys())}")
        
        return files
    
    def validate_response(self, parsed_files: Dict[str, str]) -> Tuple[bool, str]:
        """WholeFile 전략 응답 유효성 검증"""
        if not parsed_files:
            return False, "파싱된 파일이 없습니다. 완전한 파일 형식으로 응답해주세요."
        
        for file_path, content in parsed_files.items():
            # 파일 경로 유효성 검사
            if not file_path or '`' in file_path:
                return False, f"잘못된 파일 경로: {file_path}"
            
            # 내용이 너무 짧은 경우 (완전한 파일이 아닐 가능성)
            if len(content) < 10:
                return False, f"파일 내용이 너무 짧습니다: {file_path} (완전한 파일 내용을 제공해주세요)"
            
            # 명백히 부분 파일인 경우 감지
            if '...' in content or '# 나머지 코드' in content or '/* ... */' in content:
                return False, f"부분적인 파일 내용이 감지되었습니다: {file_path} (전체 파일 내용을 제공해주세요)"
        
        return True, "유효한 전체 파일 응답입니다."
    
    def supports_partial_edit(self) -> bool:
        return False  # 전체 파일만 교체
    
    def supports_multiple_files(self) -> bool:
        return True  # 여러 파일 동시 처리 가능
    
    def get_best_use_cases(self) -> List[str]:
        return [
            "작은 파일의 대규모 변경",
            "새 파일 생성",
            "전체 구조 리팩토링",
            "여러 파일의 동시 수정",
            "안전한 전체 교체"
        ]

# 레지스트리에 등록
registry.register('whole', WholeFileCoder)