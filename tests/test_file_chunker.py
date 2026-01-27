"""
FileChunker 단위 테스트
"""

import os
import sys
import unittest

# 프로젝트 루트를 path에 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from cli.core.file_chunker import (
    FileChunker,
    FileChunk,
    ChunkingResult,
    CHARS_PER_TOKEN,
    TOKEN_THRESHOLD,
    MAX_CHUNK_TOKENS,
)
from cli.core.debug_manager import DebugManager

# 테스트 중 디버그 출력 비활성화
DebugManager.set_debug_enabled(False)

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), 'fixtures')


class TestTokenEstimation(unittest.TestCase):
    """토큰 추정 테스트"""

    def test_empty_content(self):
        self.assertEqual(FileChunker.estimate_tokens(""), 0)

    def test_ascii_content(self):
        content = "a" * 350
        tokens = FileChunker.estimate_tokens(content)
        self.assertEqual(tokens, 100)

    def test_mixed_content(self):
        content = "hello world 안녕하세요"
        tokens = FileChunker.estimate_tokens(content)
        self.assertGreater(tokens, 0)


class TestNeedsChunking(unittest.TestCase):
    """청킹 필요 여부 판단 테스트"""

    def test_small_file_no_chunking(self):
        """작은 파일은 청킹하지 않음"""
        small_content = "int main() { return 0; }"
        self.assertFalse(FileChunker.needs_chunking(small_content))

    def test_empty_content(self):
        self.assertFalse(FileChunker.needs_chunking(""))

    def test_none_content(self):
        self.assertFalse(FileChunker.needs_chunking(None))

    def test_large_content(self):
        """TOKEN_THRESHOLD 이상이면 청킹 필요"""
        large_content = "x" * int(TOKEN_THRESHOLD * CHARS_PER_TOKEN + 1)
        self.assertTrue(FileChunker.needs_chunking(large_content))

    def test_small_fixture_no_chunking(self):
        """작은 C 파일(378줄)은 청킹하지 않음"""
        c_file = os.path.join(FIXTURES_DIR, 'ORDSS04S2050T01.c')
        if os.path.exists(c_file):
            with open(c_file, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            self.assertFalse(FileChunker.needs_chunking(content))


class TestLargeFileChunking(unittest.TestCase):
    """대용량 파일 청킹 테스트"""

    def setUp(self):
        self.chunker = FileChunker()
        self.pc_file = os.path.join(FIXTURES_DIR, 'zinvbreps8030_bf.pc')

    def _load_pc_file(self):
        if not os.path.exists(self.pc_file):
            self.skipTest(f"Fixture file not found: {self.pc_file}")
        with open(self.pc_file, 'r', encoding='utf-8', errors='replace') as f:
            return f.read()

    def test_large_pc_file_needs_chunking(self):
        """대용량 Pro*C 파일은 청킹이 필요함"""
        content = self._load_pc_file()
        self.assertTrue(FileChunker.needs_chunking(content))

    def test_large_pc_file_chunking(self):
        """zinvbreps8030_bf.pc를 청킹하면 3개 이상 청크 생성"""
        content = self._load_pc_file()
        result = self.chunker.chunk_file(self.pc_file, content)

        self.assertIsNotNone(result)
        self.assertIsInstance(result, ChunkingResult)
        self.assertGreaterEqual(len(result.chunks), 3)
        self.assertEqual(result.file_path, self.pc_file)
        self.assertGreater(result.total_tokens, TOKEN_THRESHOLD)

    def test_chunks_have_context_header(self):
        """각 청크에 context_header가 포함되어 있음"""
        content = self._load_pc_file()
        result = self.chunker.chunk_file(self.pc_file, content)

        if not result:
            self.skipTest("Chunking returned no result")

        # C/Pro*C 파일이므로 헤더가 있어야 함
        for chunk in result.chunks:
            self.assertIsInstance(chunk.context_header, str)

    def test_chunk_tokens_within_limit(self):
        """각 청크의 토큰 수가 MAX_CHUNK_TOKENS의 2배 이내 (과대 함수 재분할 포함)"""
        content = self._load_pc_file()
        result = self.chunker.chunk_file(self.pc_file, content)

        if not result:
            self.skipTest("Chunking returned no result")

        for chunk in result.chunks:
            # 재분할 후에도 약간의 오차 허용 (2배)
            self.assertLessEqual(
                chunk.estimated_tokens,
                MAX_CHUNK_TOKENS * 2,
                f"Chunk {chunk.chunk_index} exceeds token limit: {chunk.estimated_tokens}"
            )

    def test_chunk_line_coverage(self):
        """청크들이 파일의 상당 부분을 커버하는지 확인"""
        content = self._load_pc_file()
        result = self.chunker.chunk_file(self.pc_file, content)

        if not result:
            self.skipTest("Chunking returned no result")

        total_lines = len(content.splitlines())
        covered_lines = sum(c.end_line - c.start_line + 1 for c in result.chunks)

        # 파일의 50% 이상을 커버해야 함 (헤더/공백 제외)
        self.assertGreater(
            covered_lines,
            total_lines * 0.5,
            f"Chunks cover only {covered_lines}/{total_lines} lines"
        )


class TestFunctionBoundaries(unittest.TestCase):
    """함수 경계 탐지 테스트"""

    def setUp(self):
        self.chunker = FileChunker()

    def test_function_boundaries_pc_file(self):
        """대용량 Pro*C 파일에서 함수 경계를 탐지"""
        pc_file = os.path.join(FIXTURES_DIR, 'zinvbreps8030_bf.pc')
        if not os.path.exists(pc_file):
            self.skipTest(f"Fixture not found: {pc_file}")

        with open(pc_file, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()

        lines = content.splitlines(keepends=True)
        boundaries = self.chunker._find_function_boundaries(lines)

        # 6310줄 파일에 여러 함수가 있어야 함
        self.assertGreater(
            len(boundaries), 3,
            f"Expected more than 3 functions, found {len(boundaries)}"
        )

    def test_standard_c_function_detection(self):
        """표준 C 함수 패턴을 탐지하는지 확인"""
        sample = (
            "#include <stdio.h>\n"
            "\n"
            "void a000_init_proc(void)\n"
            "{\n"
            "    /* init */\n"
            "}\n"
            "\n"
            "int c000_main_proc(int argc)\n"
            "{\n"
            "    return 0;\n"
            "}\n"
        )
        lines = sample.splitlines(keepends=True)
        boundaries = self.chunker._find_function_boundaries(lines)

        names = [b.name for b in boundaries]
        self.assertIn('a000_init_proc', names)
        self.assertIn('c000_main_proc', names)


class TestHeaderExtraction(unittest.TestCase):
    """파일 헤더 추출 테스트"""

    def setUp(self):
        self.chunker = FileChunker()

    def test_header_extraction(self):
        """파일 헤더가 정확히 추출되는지"""
        sample = (
            "#include <stdio.h>\n"
            "#include <stdlib.h>\n"
            "#define MAX_SIZE 100\n"
            "\n"
            "/* global vars */\n"
            "int g_count = 0;\n"
            "\n"
            "void a000_init_proc(void)\n"
            "{\n"
            "    g_count = 1;\n"
            "}\n"
        )
        lines = sample.splitlines(keepends=True)
        header, header_end = self.chunker._extract_header(lines)

        # 헤더에 include가 포함되어야 함
        self.assertIn("#include", header)
        # 헤더 끝은 함수 정의 전이어야 함
        self.assertLessEqual(header_end, 8)


class TestLineBasedChunking(unittest.TestCase):
    """라인 기반 fallback 청킹 테스트"""

    def setUp(self):
        self.chunker = FileChunker()

    def test_line_based_chunking(self):
        """함수 경계가 없는 대용량 파일은 라인 기반으로 분할"""
        # 큰 XML 유사 컨텐츠 생성
        lines_content = "\n".join([f"<item id='{i}'>{i}</item>" for i in range(10000)])
        result = self.chunker._chunk_by_lines(
            "test.xml", lines_content, self.chunker.estimate_tokens(lines_content)
        )

        self.assertIsNotNone(result)
        self.assertGreater(len(result.chunks), 1)

        # 모든 청크가 빈 context_header를 가짐
        for chunk in result.chunks:
            self.assertEqual(chunk.context_header, "")


class TestChunkFileNone(unittest.TestCase):
    """엣지 케이스 테스트"""

    def test_empty_content(self):
        chunker = FileChunker()
        result = chunker.chunk_file("test.c", "")
        self.assertIsNone(result)

    def test_none_content(self):
        chunker = FileChunker()
        result = chunker.chunk_file("test.c", None)
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()
