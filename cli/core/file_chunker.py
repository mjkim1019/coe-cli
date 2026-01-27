"""
대용량 파일 청크 분석 시스템

Map-Reduce 패턴으로 대용량 파일을 함수 경계 기준으로 청크 분할하여
각 청크를 개별 LLM 호출로 분석 후 결과를 통합합니다.
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional

from .debug_manager import DebugManager

# --- 상수 ---
CHARS_PER_TOKEN = 3.5       # 한글/ASCII 혼합 코드 보수적 추정
TOKEN_THRESHOLD = 80_000    # 80K 토큰 이상이면 청킹 트리거
MAX_CHUNK_TOKENS = 25_000   # 각 청크 최대 25K 토큰
FALLBACK_CHUNK_LINES = 2500 # 라인 기반 fallback 분할 단위


@dataclass
class FileChunk:
    """파일 청크 데이터"""
    file_path: str
    chunk_index: int
    total_chunks: int
    start_line: int           # 1-based
    end_line: int             # 1-based, inclusive
    content: str
    functions: List[str]      # 이 청크에 포함된 함수 이름들
    estimated_tokens: int
    context_header: str       # 파일 헤더 (includes/defines) — 모든 청크에 공통 첨부


@dataclass
class FunctionBoundary:
    """함수 경계 정보"""
    name: str
    start_line: int  # 1-based
    end_line: int    # 1-based, inclusive


@dataclass
class ChunkingResult:
    """청킹 결과"""
    file_path: str
    total_tokens: int
    chunks: List[FileChunk]
    header: str
    function_count: int


class FileChunker:
    """대용량 파일 청크 분할 엔진"""

    @staticmethod
    def estimate_tokens(content: str) -> int:
        """문자열의 토큰 수를 추정합니다."""
        if not content:
            return 0
        return int(len(content) / CHARS_PER_TOKEN)

    @staticmethod
    def needs_chunking(content: str) -> bool:
        """파일 내용이 청킹이 필요한지 판단합니다."""
        if not content:
            return False
        return FileChunker.estimate_tokens(content) >= TOKEN_THRESHOLD

    def chunk_file(self, file_path: str, content: str) -> Optional[ChunkingResult]:
        """파일을 청크로 분할합니다.

        C/Pro*C 파일은 함수 경계 기준으로 분할하고,
        그 외 파일은 라인 기반으로 분할합니다.
        """
        if not content:
            return None

        total_tokens = self.estimate_tokens(content)
        DebugManager.chunking(
            f"파일 청킹 시작: {file_path} "
            f"(약 {total_tokens:,} tokens, {len(content):,} chars)"
        )

        ext = _get_extension(file_path)

        if ext in ('.c', '.pc', '.h'):
            return self._chunk_c_file(file_path, content, total_tokens)
        else:
            return self._chunk_by_lines(file_path, content, total_tokens)

    # ------------------------------------------------------------------
    # C / Pro*C 파일 전용 청킹
    # ------------------------------------------------------------------

    def _chunk_c_file(self, file_path: str, content: str, total_tokens: int) -> ChunkingResult:
        lines = content.splitlines(keepends=True)

        header, header_end_line = self._extract_header(lines)
        boundaries = self._find_function_boundaries(lines)

        DebugManager.chunking(
            f"C 파일 분석: 헤더 {header_end_line}줄, "
            f"함수 {len(boundaries)}개 발견"
        )

        if not boundaries:
            # 함수 경계를 찾지 못하면 라인 기반 fallback
            DebugManager.chunking("함수 경계를 찾지 못함 → 라인 기반 fallback")
            return self._chunk_by_lines(file_path, content, total_tokens)

        # 함수들을 MAX_CHUNK_TOKENS 내에서 그리디하게 그룹핑
        header_tokens = self.estimate_tokens(header)
        max_body_tokens = MAX_CHUNK_TOKENS - header_tokens

        groups: List[List[FunctionBoundary]] = []
        current_group: List[FunctionBoundary] = []
        current_tokens = 0

        for boundary in boundaries:
            func_content = "".join(lines[boundary.start_line - 1 : boundary.end_line])
            func_tokens = self.estimate_tokens(func_content)

            if current_group and current_tokens + func_tokens > max_body_tokens:
                groups.append(current_group)
                current_group = []
                current_tokens = 0

            current_group.append(boundary)
            current_tokens += func_tokens

        if current_group:
            groups.append(current_group)

        # 함수 그룹 → 청크 변환 (과대 함수는 라인 기반으로 재분할)
        raw_chunks: List[FileChunk] = []

        for group in groups:
            start_line = group[0].start_line
            end_line = group[-1].end_line
            body = "".join(lines[start_line - 1 : end_line])
            body_tokens = self.estimate_tokens(body)
            func_names = [b.name for b in group]

            if body_tokens + header_tokens <= MAX_CHUNK_TOKENS:
                raw_chunks.append(FileChunk(
                    file_path=file_path,
                    chunk_index=0,  # 나중에 재번호
                    total_chunks=0,
                    start_line=start_line,
                    end_line=end_line,
                    content=body,
                    functions=func_names,
                    estimated_tokens=body_tokens + header_tokens,
                    context_header=header,
                ))
            else:
                # 단일 함수가 너무 큼 → 라인 기반으로 재분할
                func_lines = lines[start_line - 1 : end_line]
                sub_size = int(max_body_tokens * CHARS_PER_TOKEN / max(len("".join(func_lines)) / len(func_lines), 1))
                sub_size = max(sub_size, 300)
                for s in range(0, len(func_lines), sub_size):
                    sub_end = min(s + sub_size, len(func_lines))
                    sub_body = "".join(func_lines[s:sub_end])
                    raw_chunks.append(FileChunk(
                        file_path=file_path,
                        chunk_index=0,
                        total_chunks=0,
                        start_line=start_line + s,
                        end_line=start_line + sub_end - 1,
                        content=sub_body,
                        functions=[f"{fn}(part)" for fn in func_names],
                        estimated_tokens=self.estimate_tokens(sub_body) + header_tokens,
                        context_header=header,
                    ))

        # 최종 인덱스 부여
        total_chunks = len(raw_chunks)
        chunks: List[FileChunk] = []
        for idx, chunk in enumerate(raw_chunks):
            chunk.chunk_index = idx
            chunk.total_chunks = total_chunks
            chunks.append(chunk)

            DebugManager.chunking(
                f"  청크 {idx + 1}/{total_chunks}: "
                f"lines {chunk.start_line}-{chunk.end_line}, "
                f"함수 {chunk.functions}, "
                f"약 {chunk.estimated_tokens:,} tokens"
            )

        return ChunkingResult(
            file_path=file_path,
            total_tokens=total_tokens,
            chunks=chunks,
            header=header,
            function_count=len(boundaries),
        )

    def _extract_header(self, lines: List[str]) -> tuple:
        """첫 함수 정의 전까지의 include/define/global 영역을 추출합니다.

        Returns:
            (header_text, header_end_line)  — header_end_line은 1-based
        """
        # 함수 정의 시작을 알리는 패턴들
        func_start_patterns = [
            re.compile(r'^(?:static\s+)?(?:void|int|long|char|double|float)\s+\w+\s*\('),
            re.compile(r'^\w+\s*:'),           # 'a000_init_proc :' 스타일 주석
            re.compile(r'^/\*+\s*함\s*수\s*명'),  # '/* 함 수 명 :' 스타일 주석
        ]

        header_end = 0
        for i, line in enumerate(lines):
            stripped = line.strip()
            for pat in func_start_patterns:
                if pat.search(stripped):
                    header_end = i
                    break
            else:
                continue
            break

        # 헤더가 너무 짧거나 못 찾았으면 처음 100줄 사용
        if header_end < 5:
            header_end = min(100, len(lines))

        header_text = "".join(lines[:header_end])
        return header_text, header_end

    def _find_function_boundaries(self, lines: List[str]) -> List[FunctionBoundary]:
        """C/Pro*C 파일에서 함수 시작/끝 경계를 탐지합니다.

        탐지 전략:
        1. '함 수 명 :' 주석 패턴 → 함수 시작 마커
        2. 반환 타입 + 함수명 + '(' 패턴
        3. brace depth 추적으로 함수 끝 결정
        """
        boundaries: List[FunctionBoundary] = []

        # 패턴 1: '함 수 명 : xxx' 주석 패턴 (한국어 주석 기반)
        comment_func_pattern = re.compile(
            r'/\*+\s*함\s*수\s*명\s*:\s*(\w+)', re.UNICODE
        )
        # 패턴 2: C 함수 정의 패턴
        c_func_pattern = re.compile(
            r'^(?:static\s+)?(?:void|int|long|char|double|float|short|unsigned|signed)\s+'
            r'(\w+)\s*\(',
            re.MULTILINE,
        )
        # 패턴 3: 표준 함수 이름 패턴 (a000_, b000_, c000_, z999_ 등)
        std_func_pattern = re.compile(
            r'^(?:static\s+)?(?:void|int|long|char|double|float|short|unsigned|signed)\s+'
            r'([a-z]\d{3}_\w+)\s*\(',
            re.MULTILINE,
        )

        # 먼저 모든 함수 시작 위치를 수집
        func_starts: List[tuple] = []  # (line_index_0based, func_name)

        for i, line in enumerate(lines):
            stripped = line.strip()

            # 주석 패턴 체크
            m = comment_func_pattern.search(stripped)
            if m:
                func_starts.append((i, m.group(1)))
                continue

            # C 함수 정의 패턴 체크
            m = c_func_pattern.match(stripped)
            if m:
                name = m.group(1)
                # main, printf 같은 표준 라이브러리 함수는 건너뜀
                if name not in ('main', 'printf', 'fprintf', 'sprintf', 'strlen',
                                'strcpy', 'strcat', 'memset', 'memcpy', 'malloc',
                                'free', 'calloc', 'realloc'):
                    func_starts.append((i, name))
                continue

        # 중복 제거 (같은 함수가 주석과 정의 패턴 모두에 매칭될 수 있음)
        seen_names_lines: dict = {}  # name -> line_idx
        unique_starts: List[tuple] = []
        for line_idx, name in func_starts:
            # 같은 이름이 근처 10줄 이내에 있으면 중복으로 처리
            if name in seen_names_lines:
                prev_line = seen_names_lines[name]
                if abs(line_idx - prev_line) <= 10:
                    continue
            seen_names_lines[name] = line_idx
            unique_starts.append((line_idx, name))

        if not unique_starts:
            return []

        # 함수별 끝 위치를 brace depth로 결정
        for idx, (start_line_0, func_name) in enumerate(unique_starts):
            # 다음 함수의 시작 또는 파일 끝까지 검색
            if idx + 1 < len(unique_starts):
                search_end = unique_starts[idx + 1][0]
            else:
                search_end = len(lines)

            end_line_0 = self._find_function_end(lines, start_line_0, search_end)

            boundaries.append(FunctionBoundary(
                name=func_name,
                start_line=start_line_0 + 1,  # 1-based
                end_line=end_line_0 + 1,       # 1-based
            ))

        return boundaries

    @staticmethod
    def _find_function_end(lines: List[str], start: int, max_end: int) -> int:
        """brace depth 추적으로 함수 끝 라인을 찾습니다.

        Returns:
            0-based line index of the function end
        """
        depth = 0
        found_open = False

        for i in range(start, min(max_end, len(lines))):
            line = lines[i]
            # 문자열 리터럴과 주석 내부의 중괄호는 무시 (단순화)
            for ch in line:
                if ch == '{':
                    depth += 1
                    found_open = True
                elif ch == '}':
                    depth -= 1
                    if found_open and depth == 0:
                        return i

        # 닫는 중괄호를 찾지 못하면 검색 범위 끝 반환
        return max_end - 1

    # ------------------------------------------------------------------
    # 라인 기반 fallback 청킹 (XML, SQL, 기타)
    # ------------------------------------------------------------------

    def _chunk_by_lines(self, file_path: str, content: str, total_tokens: int) -> ChunkingResult:
        """라인 기반으로 파일을 분할합니다."""
        lines = content.splitlines(keepends=True)
        total_lines = len(lines)

        # 청크당 최대 라인 수 계산
        chars_per_line = len(content) / max(total_lines, 1)
        tokens_per_line = chars_per_line / CHARS_PER_TOKEN
        max_lines_per_chunk = int(MAX_CHUNK_TOKENS / max(tokens_per_line, 0.1))
        max_lines_per_chunk = max(max_lines_per_chunk, 500)  # 최소 500줄
        max_lines_per_chunk = min(max_lines_per_chunk, FALLBACK_CHUNK_LINES)

        chunks: List[FileChunk] = []
        num_chunks = (total_lines + max_lines_per_chunk - 1) // max_lines_per_chunk

        for idx in range(num_chunks):
            start = idx * max_lines_per_chunk
            end = min(start + max_lines_per_chunk, total_lines)
            body = "".join(lines[start:end])

            chunk = FileChunk(
                file_path=file_path,
                chunk_index=idx,
                total_chunks=num_chunks,
                start_line=start + 1,
                end_line=end,
                content=body,
                functions=[],
                estimated_tokens=self.estimate_tokens(body),
                context_header="",
            )
            chunks.append(chunk)

            DebugManager.chunking(
                f"  청크 {idx + 1}/{num_chunks}: "
                f"lines {start + 1}-{end}, "
                f"약 {chunk.estimated_tokens:,} tokens"
            )

        return ChunkingResult(
            file_path=file_path,
            total_tokens=total_tokens,
            chunks=chunks,
            header="",
            function_count=0,
        )


def _get_extension(file_path: str) -> str:
    """파일 경로에서 확장자를 소문자로 반환합니다."""
    import os
    _, ext = os.path.splitext(file_path)
    return ext.lower()
