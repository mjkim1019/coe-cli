"""
UDiff Coder - 유닉스 unified diff 형식을 사용하는 편집 전략
정밀한 라인 단위 수정에 최적화됨
"""
import re
from typing import Dict, List, Tuple
from .base_coder import BaseCoder, registry
from .udiff_prompts import UDiffPrompts

class UDiffCoder(BaseCoder):
    """Unified diff 기반 편집 전략 - Git과 같은 표준 diff 형식 사용"""
    
    def get_prompts_class(self) -> UDiffPrompts:
        return UDiffPrompts()
    
    def parse_response(self, response: str, context_files: Dict[str, str]) -> Dict[str, str]:
        """AI 응답에서 unified diff 추출하여 파일에 적용"""
        files = {}
        
        print(f"[UDiff DEBUG] 파싱 시작, 응답 길이: {len(response)}")
        
        # 여러 패턴으로 diff 블록 찾기
        patterns = [
            r'```diff\s*\n(.*?)\n```',  # 표준 diff 블록
            r'```\s*\n(---.*?)\n```',   # 백틱만 있는 경우
            r'(---.*?\+\+\+.*?@@.*?)(?=\n---|\n```|\Z)',  # diff 헤더 패턴
        ]
        
        diff_matches = []
        for pattern in patterns:
            matches = re.findall(pattern, response, re.DOTALL)
            if matches:
                diff_matches.extend(matches)
                print(f"[UDiff DEBUG] 패턴 매치: {len(matches)}개 diff")
                break
        
        if not diff_matches:
            # 백틱 없는 전체 diff도 시도
            if '---' in response and '+++' in response and '@@' in response:
                diff_matches = [response]
                print(f"[UDiff DEBUG] 전체 응답을 diff로 처리")
            else:
                print(f"[UDiff DEBUG] diff 패턴 매치 실패")
                print(f"[UDiff DEBUG] 응답 미리보기: {response[:200]}...")
                return files
        
        for diff_content in diff_matches:
            parsed_files = self._parse_unified_diff(diff_content, context_files)
            files.update(parsed_files)
            print(f"[UDiff DEBUG] diff에서 {len(parsed_files)}개 파일 파싱됨")
        
        return files
    
    def _parse_unified_diff(self, diff_content: str, context_files: Dict[str, str]) -> Dict[str, str]:
        """Unified diff 형식을 파싱하여 파일별 결과 생성"""
        files = {}
        lines = diff_content.split('\n')
        
        current_file = None
        original_file = None
        hunks = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # 파일 헤더 처리
            if line.startswith('--- '):
                original_file = line[4:].strip()
                if i + 1 < len(lines) and lines[i + 1].startswith('+++ '):
                    current_file = lines[i + 1][4:].strip()
                    i += 2
                    continue
            
            # Hunk 헤더 처리 (@@ -old_start,old_count +new_start,new_count @@)
            elif line.startswith('@@'):
                if current_file:
                    hunk_match = re.match(r'@@ -(\d+),(\d+) \+(\d+),(\d+) @@', line)
                    if hunk_match:
                        old_start, old_count, new_start, new_count = map(int, hunk_match.groups())
                        
                        # Hunk 내용 수집
                        hunk_lines = []
                        i += 1
                        while i < len(lines) and not lines[i].startswith('@@') and not lines[i].startswith('---'):
                            if lines[i].startswith(' ') or lines[i].startswith('-') or lines[i].startswith('+'):
                                hunk_lines.append(lines[i])
                            i += 1
                        
                        hunks.append({
                            'old_start': old_start,
                            'old_count': old_count,
                            'new_start': new_start,
                            'new_count': new_count,
                            'lines': hunk_lines
                        })
                        continue
            
            i += 1
        
        # 파일에 hunk 적용
        if current_file and hunks:
            if current_file in context_files:
                modified_content = self._apply_hunks(context_files[current_file], hunks)
                files[current_file] = modified_content
            else:
                print(f"[UDiff DEBUG] 컨텍스트에 없는 파일: {current_file}")
        
        return files
    
    def _apply_hunks(self, original_content: str, hunks: List[Dict]) -> str:
        """Hunk들을 원본 파일에 적용"""
        lines = original_content.split('\n')
        
        # Hunk를 역순으로 적용 (뒤에서부터 적용해야 라인 번호가 안 꼬임)
        for hunk in reversed(hunks):
            old_start = hunk['old_start'] - 1  # 0-based 인덱스
            old_count = hunk['old_count']
            hunk_lines = hunk['lines']
            
            # 새로운 라인들 생성
            new_lines = []
            for hunk_line in hunk_lines:
                if hunk_line.startswith(' '):
                    # 컨텍스트 라인 (변경 없음)
                    new_lines.append(hunk_line[1:])
                elif hunk_line.startswith('+'):
                    # 추가된 라인
                    new_lines.append(hunk_line[1:])
                # '-'로 시작하는 라인은 제거되므로 new_lines에 추가하지 않음
            
            # 원본 라인 교체
            lines[old_start:old_start + old_count] = new_lines
        
        return '\n'.join(lines)
    
    def validate_response(self, parsed_files: Dict[str, str]) -> Tuple[bool, str]:
        """UDiff 전략 응답 유효성 검증"""
        if not parsed_files:
            return False, "Unified diff 블록이 파싱되지 않았습니다."
        
        return True, "UDiff 응답이 유효합니다."
    
    def supports_partial_edit(self) -> bool:
        return True  # 부분 편집 특화
    
    def supports_multiple_files(self) -> bool:
        return True  # 여러 파일 지원
    
    def get_best_use_cases(self) -> List[str]:
        return [
            "정밀한 라인 단위 수정",
            "버전 관리 친화적 변경",
            "표준 patch 형식 적용",
            "복잡한 다중 위치 수정",
            "Git workflow 통합"
        ]

# 레지스트리에 등록
registry.register('udiff', UDiffCoder)