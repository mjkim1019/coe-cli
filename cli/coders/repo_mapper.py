"""
RepoMapper - baseCoder를 위한 경량 레포지토리 맵 생성기
Aider의 repomap 기능을 참고하여 Swing CLI에 최적화
"""
import os
import re
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
from collections import defaultdict, Counter
from ..core.debug_manager import DebugManager


class RepoMapper:
    """경량 레포지토리 맵 생성기 - baseCoder 내부 사용"""

    def __init__(self, root_path: str = "."):
        self.root_path = Path(root_path).resolve()
        self._symbol_cache = {}
        self._file_cache = {}

        # 제외할 디렉토리와 파일
        self.exclude_dirs = {
            '.git', '.venv', '__pycache__', 'node_modules',
            '.pytest_cache', 'dist', 'build', '.coverage'
        }
        self.exclude_extensions = {
            '.pyc', '.pyo', '.pyd', '.so', '.dylib', '.dll', '.exe'
        }

    def generate_map(self,
                     chat_files: Optional[List[str]] = None,
                     other_files: Optional[List[str]] = None,
                     mentioned_fnames: Optional[List[str]] = None,
                     mentioned_idents: Optional[List[str]] = None,
                     force_refresh: bool = False) -> str:
        """레포지토리 맵 생성"""

        DebugManager.repo_map("레포맵 생성 시작")
        DebugManager.repo_map(f"- chat_files: {chat_files}")
        DebugManager.repo_map(f"- other_files: {other_files[:5] if other_files else None}{'...' if other_files and len(other_files) > 5 else ''}")
        DebugManager.repo_map(f"- mentioned_fnames: {mentioned_fnames}")
        DebugManager.repo_map(f"- mentioned_idents: {mentioned_idents}")

        if force_refresh:
            self._clear_cache()

        # 우선순위 파일 수집
        priority_files = self._collect_priority_files(
            chat_files, other_files, mentioned_fnames
        )
        DebugManager.repo_map(f"우선순위 파일 {len(priority_files)}개 수집: {priority_files[:3]}{'...' if len(priority_files) > 3 else ''}")

        # 파일 분석
        file_symbols = self._analyze_files(priority_files)
        DebugManager.repo_map(f"{len(file_symbols)}개 파일 분석 완료")

        # 중요 심볼 추출
        important_symbols = self._extract_important_symbols(
            file_symbols, mentioned_idents
        )
        DebugManager.repo_map(f"중요 심볼 {len(important_symbols)}개 추출: {important_symbols[:5]}{'...' if len(important_symbols) > 5 else ''}")

        # 컴팩트 맵 생성
        repo_map = self._build_compact_map(file_symbols, important_symbols)
        DebugManager.repo_map(f"레포맵 생성 완료 ({len(repo_map)} chars)")

        return repo_map

    def _collect_priority_files(self,
                                chat_files: Optional[List[str]] = None,
                                other_files: Optional[List[str]] = None,
                                mentioned_fnames: Optional[List[str]] = None) -> List[str]:
        """우선순위에 따라 파일 수집"""
        files = []

        # 1순위: chat_files
        if chat_files:
            files.extend(chat_files)

        # 2순위: mentioned_fnames
        if mentioned_fnames:
            files.extend(mentioned_fnames)

        # 3순위: other_files
        if other_files:
            files.extend(other_files)

        # 중복 제거
        unique_files = []
        seen = set()
        for f in files:
            if f not in seen:
                seen.add(f)
                unique_files.append(f)

        # 파일이 없으면 주요 파일들만 스캔
        if not unique_files:
            unique_files = self._scan_key_files()

        return unique_files[:20]  # 최대 20개 파일로 제한

    def _scan_key_files(self) -> List[str]:
        """tests/fixtures 파일들만 스캔"""
        key_files = []

        # tests/fixtures 디렉토리만 스캔
        fixtures_path = self.root_path / 'tests' / 'fixtures'
        if not fixtures_path.exists():
            DebugManager.repo_map("tests/fixtures 디렉토리를 찾을 수 없음")
            return []

        DebugManager.repo_map(f"tests/fixtures 디렉토리 스캔: {fixtures_path}")

        for root, dirs, filenames in os.walk(fixtures_path):
            # 제외 디렉토리 필터링
            dirs[:] = [d for d in dirs if d not in self.exclude_dirs]

            for filename in filenames:
                file_path = Path(root) / filename
                rel_path = file_path.relative_to(self.root_path)

                # 제외 확장자 체크
                if file_path.suffix in self.exclude_extensions:
                    continue

                # 주요 파일 타입만 포함
                if self._is_code_file(file_path):
                    key_files.append(str(rel_path))

        DebugManager.repo_map(f"fixtures에서 {len(key_files)}개 파일 발견")
        return sorted(key_files)[:50]  # 최대 50개

    def _is_code_file(self, file_path: Path) -> bool:
        """코드 파일인지 확인"""
        code_extensions = {
            '.py', '.c', '.h', '.cpp', '.hpp', '.java', '.js', '.ts',
            '.xml', '.sql', '.go', '.rs', '.php', '.rb', '.swift'
        }
        return file_path.suffix in code_extensions

    def _analyze_files(self, files: List[str]) -> Dict[str, Dict]:
        """파일들 분석하여 심볼 정보 수집"""
        file_symbols = {}

        for file_path in files:
            full_path = self.root_path / file_path
            if not full_path.exists():
                DebugManager.repo_map(f"파일 없음: {file_path}")
                continue

            # 캐시 확인
            cache_key = f"{file_path}:{full_path.stat().st_mtime}"
            if cache_key in self._file_cache:
                file_symbols[file_path] = self._file_cache[cache_key]
                DebugManager.repo_map(f"캐시에서 로드: {file_path}")
                continue

            # 파일 내용 head 미리보기 (디버그용)
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                head_lines = content.split('\n')[:5]  # 처음 5줄
                head_preview = '\n'.join(head_lines)
                if len(head_preview) > 150:
                    head_preview = head_preview[:150] + "..."
                DebugManager.repo_map(f"분석 중: {file_path} ({len(content)} chars)")
                DebugManager.repo_map(f"Head: {repr(head_preview)}")
            except Exception as e:
                DebugManager.error(f"파일 읽기 실패: {file_path} - {e}")
                continue

            # 파일 타입별 분석
            symbols = self._analyze_single_file(full_path)
            if symbols:
                file_symbols[file_path] = symbols
                self._file_cache[cache_key] = symbols
                DebugManager.repo_map(f"분석 완료: {file_path} - {sum(len(v) if isinstance(v, list) else 0 for v in symbols.values())}개 심볼")

        return file_symbols

    def _analyze_single_file(self, file_path: Path) -> Dict:
        """단일 파일 분석"""
        ext = file_path.suffix.lower()

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception:
            return {}

        if ext == '.py':
            return self._analyze_python(content)
        elif ext in ['.c', '.h']:
            return self._analyze_c(content)
        elif ext in ['.cpp', '.hpp']:
            return self._analyze_cpp(content)
        elif ext == '.java':
            return self._analyze_java(content)
        elif ext in ['.js', '.ts']:
            return self._analyze_javascript(content)
        elif ext == '.xml':
            return self._analyze_xml(content)
        elif ext == '.sql':
            return self._analyze_sql(content)
        else:
            return self._analyze_generic(content)

    def _analyze_python(self, content: str) -> Dict:
        """Python 파일 분석"""
        symbols = {'functions': [], 'classes': []}

        # 함수 정의
        func_pattern = r'^def\s+(\w+)\s*\('
        for match in re.finditer(func_pattern, content, re.MULTILINE):
            symbols['functions'].append(match.group(1))

        # 클래스 정의
        class_pattern = r'^class\s+(\w+)(?:\([^)]*\))?:'
        for match in re.finditer(class_pattern, content, re.MULTILINE):
            symbols['classes'].append(match.group(1))

        return symbols

    def _analyze_c(self, content: str) -> Dict:
        """C 파일 분석"""
        symbols = {'functions': [], 'structs': []}

        # 함수 정의 (C 스타일)
        func_pattern = r'(?:static\s+)?(?:long|int|void|char\*?)\s+(\w+)\s*\([^)]*\)\s*{'
        for match in re.finditer(func_pattern, content):
            symbols['functions'].append(match.group(1))

        # 구조체 정의
        struct_pattern = r'typedef\s+struct.*?(\w+_t)\s*;'
        for match in re.finditer(struct_pattern, content, re.DOTALL):
            symbols['structs'].append(match.group(1))

        return symbols

    def _analyze_cpp(self, content: str) -> Dict:
        """C++ 파일 분석"""
        symbols = self._analyze_c(content)

        # 클래스 정의 추가
        symbols['classes'] = []
        class_pattern = r'class\s+(\w+)(?:\s*:\s*[^{]*)?{'
        for match in re.finditer(class_pattern, content):
            symbols['classes'].append(match.group(1))

        return symbols

    def _analyze_java(self, content: str) -> Dict:
        """Java 파일 분석"""
        symbols = {'classes': [], 'methods': []}

        # 클래스 정의
        class_pattern = r'(?:public\s+)?class\s+(\w+)'
        for match in re.finditer(class_pattern, content):
            symbols['classes'].append(match.group(1))

        # 메서드 정의
        method_pattern = r'(?:public|private|protected)?\s*(?:static\s+)?[\w<>]+\s+(\w+)\s*\([^)]*\)\s*{'
        for match in re.finditer(method_pattern, content):
            symbols['methods'].append(match.group(1))

        return symbols

    def _analyze_javascript(self, content: str) -> Dict:
        """JavaScript/TypeScript 파일 분석"""
        symbols = {'functions': [], 'classes': []}

        # 함수 정의
        func_patterns = [
            r'function\s+(\w+)\s*\(',
            r'const\s+(\w+)\s*=\s*(?:async\s+)?(?:\([^)]*\)|[\w,\s]+)\s*=>'
        ]

        for pattern in func_patterns:
            for match in re.finditer(pattern, content):
                symbols['functions'].append(match.group(1))

        # 클래스 정의
        class_pattern = r'class\s+(\w+)'
        for match in re.finditer(class_pattern, content):
            symbols['classes'].append(match.group(1))

        return symbols

    def _analyze_xml(self, content: str) -> Dict:
        """XML 파일 분석"""
        symbols = {'elements': [], 'scripts': []}

        # 주요 XML 요소
        element_pattern = r'<(\w+)(?:\s+[^>]*)?>'
        elements = set()
        for match in re.finditer(element_pattern, content):
            elements.add(match.group(1))
        symbols['elements'] = list(elements)[:10]  # 상위 10개만

        # 스크립트 함수 (scwin 등)
        script_pattern = r'(\w+\.\w+)\s*\('
        scripts = set()
        for match in re.finditer(script_pattern, content):
            scripts.add(match.group(1))
        symbols['scripts'] = list(scripts)[:10]

        return symbols

    def _analyze_sql(self, content: str) -> Dict:
        """SQL 파일 분석"""
        symbols = {'tables': [], 'bind_vars': []}

        # 테이블 찾기
        table_pattern = r'FROM\s+(\w+)|JOIN\s+(\w+)'
        tables = set()
        for match in re.finditer(table_pattern, content, re.IGNORECASE):
            table = match.group(1) or match.group(2)
            if table:
                tables.add(table)
        symbols['tables'] = list(tables)

        # 바인드 변수
        bind_pattern = r':(\w+)'
        bind_vars = set()
        for match in re.finditer(bind_pattern, content):
            bind_vars.add(match.group(1))
        symbols['bind_vars'] = list(bind_vars)

        return symbols

    def _analyze_generic(self, content: str) -> Dict:
        """일반 텍스트 파일 분석"""
        symbols = {'identifiers': []}

        # 기본 식별자 패턴
        identifier_pattern = r'\b[a-zA-Z_]\w{2,}\b'
        identifiers = set()
        for match in re.finditer(identifier_pattern, content):
            ident = match.group()
            if len(ident) > 2:
                identifiers.add(ident)

        symbols['identifiers'] = list(identifiers)[:20]  # 상위 20개
        return symbols

    def _extract_important_symbols(self, file_symbols: Dict[str, Dict], mentioned_idents: Optional[List[str]] = None) -> List[str]:
        """중요한 심볼들 추출"""
        symbol_counts = Counter()

        # 모든 심볼 수집
        for file_path, symbols in file_symbols.items():
            for symbol_type, symbol_list in symbols.items():
                for symbol in symbol_list:
                    if isinstance(symbol, str) and len(symbol) > 2:
                        symbol_counts[symbol] += 1

        # 언급된 식별자는 가중치 부여
        if mentioned_idents:
            for ident in mentioned_idents:
                if ident in symbol_counts:
                    symbol_counts[ident] += 5

        return [symbol for symbol, count in symbol_counts.most_common(15)]

    def _build_compact_map(self, file_symbols: Dict[str, Dict], important_symbols: List[str]) -> str:
        """컴팩트한 레포지토리 맵 생성"""
        lines = []

        # 중요 심볼들
        if important_symbols:
            lines.append("Key Symbols:")
            for symbol in important_symbols[:10]:
                lines.append(f"  • {symbol}")
            lines.append("")

        # 파일별 구조 (간략화)
        lines.append("File Overview:")
        for file_path, symbols in list(file_symbols.items())[:10]:
            lines.append(f"  {file_path}:")

            # 각 심볼 타입별 요약
            for symbol_type, symbol_list in symbols.items():
                if symbol_list:
                    count = len(symbol_list)
                    sample = symbol_list[:3]  # 상위 3개만 표시
                    if count <= 3:
                        lines.append(f"    {symbol_type}: {', '.join(sample)}")
                    else:
                        lines.append(f"    {symbol_type}: {', '.join(sample)} (+{count-3} more)")

        return "\n".join(lines)

    def _clear_cache(self):
        """캐시 클리어"""
        self._symbol_cache.clear()
        self._file_cache.clear()