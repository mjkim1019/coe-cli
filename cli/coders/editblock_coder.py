"""
EditBlock Coder - 특정 코드 블록만 정밀하게 교체하는 편집 전략
큰 파일의 부분 수정에 최적화됨
"""
import re
from typing import Dict, List, Tuple
from .base_coder import BaseCoder, registry
from .editblock_prompts import EditBlockPrompts

class EditBlockCoder(BaseCoder):
    """블록 기반 편집 전략 - 특정 코드 블록만 찾아서 교체"""
    
    def get_prompts_class(self) -> EditBlockPrompts:
        return EditBlockPrompts()
    
    def parse_response(self, response: str, context_files: Dict[str, str]) -> Dict[str, str]:
        """AI 응답에서 SEARCH/REPLACE 블록 추출하여 파일 적용"""
        files = {}
        
        # 파일별 편집 블록 찾기
        file_pattern = r'^([^\s\n<]+\.[a-zA-Z0-9]+)\s*\n((?:<<<<<<< SEARCH.*?>>>>>>> REPLACE\s*\n?)+)'
        file_matches = re.findall(file_pattern, response, re.MULTILINE | re.DOTALL)
        
        for file_path, blocks_content in file_matches:
            file_path = file_path.strip()
            
            if file_path not in context_files:
                print(f"[EditBlock DEBUG] 컨텍스트에 없는 파일: {file_path}")
                continue
                
            original_content = context_files[file_path]
            modified_content = original_content
            
            # 각 SEARCH/REPLACE 블록 처리
            block_pattern = r'<<<<<<< SEARCH\s*\n(.*?)\n=======\s*\n(.*?)\n>>>>>>> REPLACE'
            blocks = re.findall(block_pattern, blocks_content, re.DOTALL)
            
            print(f"[EditBlock DEBUG] {file_path}에서 {len(blocks)}개 블록 발견")
            
            for i, (search_block, replace_block) in enumerate(blocks):
                search_block = search_block.rstrip()
                replace_block = replace_block.rstrip()
                
                # 검색 블록을 파일에서 찾기
                if search_block in modified_content:
                    modified_content = modified_content.replace(search_block, replace_block, 1)
                    print(f"[EditBlock DEBUG] 블록 {i+1} 교체 성공")
                else:
                    print(f"[EditBlock DEBUG] 블록 {i+1} 찾기 실패:")
                    print(f"[EditBlock DEBUG] 검색: '{search_block[:100]}...'")
                    
                    # 유사한 텍스트 찾기 시도 (공백 차이 무시)
                    normalized_search = ' '.join(search_block.split())
                    content_lines = modified_content.split('\n')
                    
                    for line_num, line in enumerate(content_lines):
                        normalized_line = ' '.join(line.split())
                        if normalized_search in normalized_line:
                            print(f"[EditBlock DEBUG] 유사한 라인 {line_num}: '{line}'")
                            break
            
            files[file_path] = modified_content
        
        return files
    
    def validate_response(self, parsed_files: Dict[str, str]) -> Tuple[bool, str]:
        """EditBlock 전략 응답 유효성 검증"""
        if not parsed_files:
            return False, "SEARCH/REPLACE 블록이 파싱되지 않았습니다."
        
        return True, "EditBlock 응답이 유효합니다."
    
    def supports_partial_edit(self) -> bool:
        return True  # 부분 편집 특화
    
    def supports_multiple_files(self) -> bool:
        return True  # 여러 파일 지원
    
    def get_best_use_cases(self) -> List[str]:
        return [
            "큰 파일의 부분 수정",
            "함수나 메서드 수정",
            "정밀한 타겟 변경",
            "기존 코드 보존이 중요한 경우",
            "여러 위치의 동일 패턴 수정"
        ]

# 레지스트리에 등록
registry.register('editblock', EditBlockCoder)