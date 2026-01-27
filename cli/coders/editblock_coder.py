"""
EditBlock Coder - 특정 코드 블록만 정밀하게 교체하는 편집 전략
큰 파일의 부분 수정에 최적화됨
"""
import re
from typing import Dict, List, Tuple
from .base_coder import BaseCoder, registry
from .editblock_prompts import EditBlockPrompts
from ..core.debug_manager import DebugManager

class EditBlockCoder(BaseCoder):
    """블록 기반 편집 전략 - 특정 코드 블록만 찾아서 교체"""
    
    def get_prompts_class(self) -> EditBlockPrompts:
        return EditBlockPrompts()
    
    def parse_response(self, response: str, context_files: Dict[str, str]) -> Dict[str, str]:
        """AI 응답에서 SEARCH/REPLACE 블록 추출하여 파일 적용"""
        files = {}
        
        DebugManager.info(f"[EditBlock] 파싱 시작, 응답 길이: {len(response)}")
        
        # 여러 패턴으로 파일별 편집 블록 찾기
        patterns = [
            # 표준 패턴: 파일명 다음 줄에 바로 블록
            r'^([^\s\n<]+\.[a-zA-Z0-9]+)\s*\n((?:<<<<<<< SEARCH.*?>>>>>>> REPLACE\s*\n?)+)',
            # 파일명과 블록 사이에 빈 줄이 있는 경우
            r'^([^\s\n<]+\.[a-zA-Z0-9]+)\s*\n\s*\n((?:<<<<<<< SEARCH.*?>>>>>>> REPLACE\s*\n?)+)',
            # 파일명 앞에 텍스트가 있는 경우
            r'(?:^|\n)([^\s\n<]+\.[a-zA-Z0-9]+)\s*\n((?:<<<<<<< SEARCH.*?>>>>>>> REPLACE\s*\n?)+)'
        ]
        
        file_matches = []
        for pattern in patterns:
            matches = re.findall(pattern, response, re.MULTILINE | re.DOTALL)
            file_matches.extend(matches)
            if matches:
                DebugManager.info(f"[EditBlock] 패턴 매치: {len(matches)}개 파일")
                break
        
        if not file_matches:
            DebugManager.info(f"[EditBlock] 파일 패턴 매치 실패")
            DebugManager.info(f"[EditBlock] 응답 미리보기: {response[:200]}...")
            
            # 단순히 SEARCH/REPLACE 블록만 찾아보기
            simple_blocks = re.findall(r'<<<<<<< SEARCH(.*?)>>>>>>> REPLACE', response, re.DOTALL)
            if simple_blocks:
                DebugManager.info(f"[EditBlock] 단순 블록 {len(simple_blocks)}개 발견, 컨텍스트 파일에서 매칭 시도")
                # 첫 번째 컨텍스트 파일에 적용 시도
                if context_files:
                    first_file = list(context_files.keys())[0]
                    files[first_file] = self._apply_simple_blocks(context_files[first_file], simple_blocks)
            
            # SEARCH/REPLACE 실패 시 WholeFile 패턴으로 fallback 시도
            if not files:
                DebugManager.info(f"[EditBlock] SEARCH/REPLACE 실패, WholeFile 패턴 시도")
                wholefile_patterns = [
                    r'^([^\n]+\.[a-zA-Z0-9]+)\s*\n```[a-zA-Z]*\n(.*?)\n```',  # 파일명 + 코드블록
                    r'```[a-zA-Z]*\n(.*?)\n```',  # 코드블록만
                ]
                
                for pattern in wholefile_patterns:
                    matches = re.findall(pattern, response, re.DOTALL | re.MULTILINE)
                    if matches:
                        if isinstance(matches[0], tuple) and len(matches[0]) == 2:  # 파일명 + 내용
                            file_path, content = matches[0]
                            file_path = file_path.strip().rstrip(',').strip()
                        else:  # 내용만
                            content = matches[0]
                            file_path = list(context_files.keys())[0] if context_files else 'unknown.txt'
                        
                        DebugManager.info(f"[EditBlock] WholeFile 패턴 매치: {file_path}")
                        # 컨텍스트에 있는 파일이면 사용, 없으면 첫 번째 파일 사용
                        if file_path in context_files:
                            target_file = file_path
                        elif context_files:
                            target_file = list(context_files.keys())[0]
                            DebugManager.info(f"[EditBlock] {file_path} -> {target_file} 로 매핑")
                        else:
                            continue
                            
                        files[target_file] = content.strip()
                        DebugManager.info(f"[EditBlock] WholeFile fallback 성공")
                        break
            
            return files
        
        for file_path, blocks_content in file_matches:
            file_path = file_path.strip()

            # 파일 경로를 여러 방식으로 매칭 시도
            target_file = None
            if file_path in context_files:
                target_file = file_path
            else:
                # 파일명만으로 매칭 시도
                filename = file_path.split('/')[-1]
                for ctx_file in context_files.keys():
                    if ctx_file.endswith(filename) or ctx_file.split('/')[-1] == filename:
                        target_file = ctx_file
                        DebugManager.info(f"[EditBlock] 파일명으로 매칭: {file_path} -> {target_file}")
                        break

            if not target_file:
                DebugManager.info(f"[EditBlock] 컨텍스트에 없는 파일: {file_path}")
                DebugManager.info(f"[EditBlock] 사용 가능한 파일들: {list(context_files.keys())}")
                continue

            original_content = context_files[target_file]
            modified_content = original_content
            
            # 각 SEARCH/REPLACE 블록 처리
            block_pattern = r'<<<<<<< SEARCH\s*\n(.*?)\n=======\s*\n(.*?)\n>>>>>>> REPLACE'
            blocks = re.findall(block_pattern, blocks_content, re.DOTALL)
            
            DebugManager.info(f"[EditBlock] {file_path}에서 {len(blocks)}개 블록 발견")
            
            for i, (search_block, replace_block) in enumerate(blocks):
                search_block = search_block.rstrip()
                replace_block = replace_block.rstrip()

                # 1차: 정확한 문자열 매칭
                if search_block in modified_content:
                    modified_content = modified_content.replace(search_block, replace_block, 1)
                    DebugManager.info(f"[EditBlock] 블록 {i+1} 교체 성공 (정확 매칭)")
                else:
                    DebugManager.info(f"[EditBlock] 블록 {i+1} 정확 매칭 실패, 퍼지 매칭 시도")
                    DebugManager.info(f"[EditBlock] 검색: '{search_block[:100]}...'")

                    # 2차: 줄 단위 정규화 매칭 (앞뒤 공백 무시)
                    result = self._fuzzy_replace(modified_content, search_block, replace_block)
                    if result is not None:
                        modified_content = result
                        DebugManager.info(f"[EditBlock] 블록 {i+1} 교체 성공 (퍼지 매칭)")
                    else:
                        DebugManager.info(f"[EditBlock] 블록 {i+1} 찾기 실패")
            
            files[target_file] = modified_content
        
        return files
    
    def _fuzzy_replace(self, content: str, search_block: str, replace_block: str) -> str:
        """줄 단위 정규화 매칭으로 SEARCH 블록을 찾아 교체

        LLM이 반환한 SEARCH 블록의 들여쓰기가 원본과 다를 때 사용.
        각 줄의 strip() 결과를 비교하되, 교체 시에는 원본 들여쓰기를 보존한다.
        """
        search_lines = search_block.split('\n')
        replace_lines = replace_block.split('\n')
        content_lines = content.split('\n')

        # 빈 줄만 있는 search는 매칭하지 않음
        stripped_search = [line.strip() for line in search_lines]
        if not any(stripped_search):
            return None

        for i in range(len(content_lines) - len(search_lines) + 1):
            match = True
            for j, search_line in enumerate(search_lines):
                if content_lines[i + j].strip() != search_line.strip():
                    match = False
                    break

            if match:
                # 원본의 첫 번째 줄 들여쓰기를 감지하여 REPLACE 블록에 적용
                original_indent = ''
                for ch in content_lines[i]:
                    if ch in (' ', '\t'):
                        original_indent += ch
                    else:
                        break

                # REPLACE 블록의 공통 들여쓰기 제거 후 원본 들여쓰기 적용
                replace_indent = ''
                for line in replace_lines:
                    if line.strip():
                        for ch in line:
                            if ch in (' ', '\t'):
                                replace_indent += ch
                            else:
                                break
                        break

                adjusted_replace = []
                for line in replace_lines:
                    if not line.strip():
                        adjusted_replace.append(content_lines[i].rstrip() if not content_lines[i].strip() else '')
                    elif line.startswith(replace_indent):
                        adjusted_replace.append(original_indent + line[len(replace_indent):])
                    else:
                        adjusted_replace.append(line)

                new_lines = content_lines[:i] + adjusted_replace + content_lines[i + len(search_lines):]
                return '\n'.join(new_lines)

        return None

    def _apply_simple_blocks(self, original_content: str, blocks: List[str]) -> str:
        """단순 SEARCH/REPLACE 블록들을 파일에 적용"""
        modified_content = original_content
        
        for block in blocks:
            # SEARCH와 REPLACE 부분 분리
            parts = block.split('\n=======\n')
            if len(parts) != 2:
                continue
                
            search_part = parts[0].strip()
            replace_part = parts[1].strip()
            
            # 각 줄 앞의 공백 제거하고 매칭 시도
            search_lines = [line.strip() for line in search_part.split('\n') if line.strip()]
            replace_lines = [line.strip() for line in replace_part.split('\n') if line.strip()]
            
            # 원본에서 검색
            content_lines = modified_content.split('\n')
            for i in range(len(content_lines) - len(search_lines) + 1):
                match = True
                for j, search_line in enumerate(search_lines):
                    if content_lines[i + j].strip() != search_line:
                        match = False
                        break
                
                if match:
                    # 매치된 부분을 교체
                    new_lines = content_lines[:i] + replace_lines + content_lines[i + len(search_lines):]
                    modified_content = '\n'.join(new_lines)
                    DebugManager.info(f"[EditBlock] 단순 블록 매칭 성공, {len(search_lines)}줄 -> {len(replace_lines)}줄")
                    break
        
        return modified_content
    
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
registry.register('block', EditBlockCoder)