# actions/file_manager.py
import os
import re
from typing import List, Optional, Dict
from .file_tree_analyzer import FileTreeAnalyzer

# 새로 추가: charset_normalizer로 인코딩 감지
try:
    from charset_normalizer import from_bytes
except ImportError:
    from_bytes = None

class FileManager:
    def __init__(self):
        self.files = {}
        self.c_file_info = {}  # C 파일의 구조 정보를 저장
        self.sql_file_info = {}  # SQL 파일의 구조 정보를 저장
        self.tree_analyzer = FileTreeAnalyzer()  # 파일 트리 분석기

    def add(self, file_paths):
        """파일 또는 디렉토리를 컨텍스트에 추가"""
        messages = []
        file_analyses = []
        
        for file_path in file_paths:
            if os.path.isdir(file_path):
                # 디렉토리인 경우 재귀적으로 파일들을 추가
                dir_messages = self.add_directory(file_path)
                messages.extend(dir_messages)
            else:
                # 개별 파일 처리
                result = self.add_single_file(file_path)
                if result['message']:
                    messages.append(result['message'])
                    
                # 분석 결과가 있으면 저장
                if result['analysis']:
                    file_analyses.append({
                        'file_path': file_path,
                        'file_type': result['file_type'],
                        'analysis': result['analysis']
                    })
        
        # 파일 분석 결과를 포함한 전체 결과 반환
        return {
            'messages': messages,
            'analyses': file_analyses
        }

    def add_directory(self, directory_path: str, max_files: int = 50) -> List[str]:
        """디렉토리의 파일들을 재귀적으로 추가"""
        messages = []
        
        # 디렉토리 분석
        analysis = self.tree_analyzer.analyze_directory(directory_path)
        
        if 'error' in analysis:
            messages.append(f"Error analyzing directory {directory_path}: {analysis['error']}")
            return messages
        
        # 주요 파일들을 우선적으로 추가
        primary_files = []
        other_files = []
        
        file_categories = analysis.get('file_categories', {})
        
        # 카테고리별로 파일들 분류
        for category, files in file_categories.items():
            if category in ['c_files', 'header_files', 'sql_files', 'xml_files']:
                # 주요 파일들
                for file_info in files:
                    primary_files.append(file_info['full_path'])
            else:
                # 기타 파일들
                for file_info in files:
                    other_files.append(file_info['full_path'])
        
        # 주요 파일들 먼저 추가
        added_count = 0
        for file_path in primary_files:
            if added_count >= max_files:
                break
            result = self.add_single_file(file_path)
            if result['message']:
                messages.append(result['message'])
                added_count += 1
        
        # 남은 용량이 있으면 기타 파일들도 추가
        for file_path in other_files:
            if added_count >= max_files:
                break
            result = self.add_single_file(file_path)
            if result['message']:
                messages.append(result['message'])
                added_count += 1
        
        # 디렉토리 분석 요약 추가
        insights = analysis.get('project_insights', {})
        if insights:
            messages.append(f"\n📁 Directory Analysis for {directory_path}:")
            messages.append(f"  - Project Type: {insights.get('project_type', 'unknown')}")
            messages.append(f"  - Complexity: {insights.get('complexity', 'unknown')}")
            if insights.get('characteristics'):
                messages.append(f"  - Characteristics: {', '.join(insights['characteristics'])}")
            if insights.get('tech_stack'):
                messages.append(f"  - Tech Stack: {', '.join(insights['tech_stack'])}")
        
        # 추가된 파일 통계
        total_files = analysis.get('total_files', 0)
        if added_count < total_files:
            messages.append(f"\n⚠️  Added {added_count} out of {total_files} files (limit: {max_files})")
        else:
            messages.append(f"\n✅ Added all {added_count} files from directory")
        
        return messages

    def add_single_file(self, file_path: str) -> Dict:
        """단일 파일을 컨텍스트에 추가하고 분석 결과 반환"""
        result = {
            'message': '',
            'analysis': None,
            'file_type': 'unknown'
        }
        
        if os.path.exists(file_path):
            try:
                # 바이너리 모드로 먼저 읽어 raw 데이터를 확보
                with open(file_path, 'rb') as f:
                    raw_data = f.read()

                # 1) 기본적으로 raw 데이터를 대상으로 인코딩 감지 시도
                detected_encoding = None
                if from_bytes:
                    try:
                        best_match = from_bytes(raw_data).best()
                        if best_match and best_match.encoding:
                            detected_encoding = best_match.encoding
                    except Exception:
                        pass

                # 2) 감지된 인코딩을 먼저 시도하고, 그 밖에 일반적으로 사용하는 인코딩 목록을 순차적으로 시도
                encodings_to_try = []
                if detected_encoding:
                    encodings_to_try.append(detected_encoding)
                # EUC-KR, CP949 같은 한글 인코딩과 UTF-8 BOM 등을 포함해 시도
                encodings_to_try += ['utf-8', 'utf-8-sig', 'cp949', 'euc-kr', 'shift_jis']

                content = None
                used_encoding = None
                for enc in encodings_to_try:
                    try:
                        content = raw_data.decode(enc)
                        used_encoding = enc
                        break
                    except Exception:
                        continue

                # 3) 모든 시도가 실패한 경우에는 errors='replace' 옵션을 사용해 UTF-8로 강제 디코딩
                if content is None:
                    content = raw_data.decode('utf-8', errors='replace')
                    used_encoding = 'utf-8 (fallback with replace)'

                # 읽은 내용과 인코딩 정보를 저장
                self.files[file_path] = content
                line_count = len(content.splitlines())
                char_count = len(content)
                
                # .c 파일인 경우 구조 정보 추가
                if file_path.endswith('.c'):
                    result['file_type'] = 'c_file'
                    analysis = self._analyze_c_file_structure(content)
                    self.c_file_info[file_path] = analysis
                    result['analysis'] = self._enhance_c_file_analysis(content, analysis)
                    result['message'] = (
                        f"Read C file {file_path} with encoding {used_encoding} "
                        f"({line_count} lines, {char_count} chars) - Standard C structure detected"
                    )
                # .sql 파일인 경우 구조 정보 추가
                elif file_path.endswith('.sql'):
                    result['file_type'] = 'sql_file'
                    analysis = self._analyze_sql_file_structure(content)
                    self.sql_file_info[file_path] = analysis
                    result['analysis'] = analysis
                    result['message'] = (
                        f"Read SQL file {file_path} with encoding {used_encoding} "
                        f"({line_count} lines, {char_count} chars) - Oracle SQL structure detected"
                    )
                # .h 파일인 경우 헤더 구조 분석
                elif file_path.endswith('.h'):
                    result['file_type'] = 'header_file'
                    result['analysis'] = self._analyze_header_file_structure(content, file_path)
                    result['message'] = (
                        f"Read Header file {file_path} with encoding {used_encoding} "
                        f"({line_count} lines, {char_count} chars) - Header structure detected"
                    )
                # .xml 파일인 경우 UI 구조 분석
                elif file_path.lower().endswith('.xml'):
                    result['file_type'] = 'xml_file'
                    result['analysis'] = self._analyze_xml_file_structure(content)
                    result['message'] = (
                        f"Read XML file {file_path} with encoding {used_encoding} "
                        f"({line_count} lines, {char_count} chars) - XML UI structure detected"
                    )
                else:
                    result['message'] = (
                        f"Read {file_path} with encoding {used_encoding} "
                        f"({line_count} lines, {char_count} chars)"
                    )
                    
            except Exception as e:
                result['message'] = f"Error reading file {file_path}: {e}"
        else:
            # 새 파일의 경우 빈 문자열로 초기화
            self.files[file_path] = ""
            result['message'] = f"Added new file (will be created on edit): {file_path}"
            
        return result

    def _analyze_c_file_structure(self, content):
        """C 파일의 표준 함수 구조를 분석"""
        standard_functions = {
            'a000_init_proc': '프로그램 초기화 함수',
            'b000_input_validation': '입력 데이터 검증 수행',
            'b999_output_setting': '출력 전문의 순서 설정',
            'c000_main_proc': '실제 프로그램의 주요 로직 처리',
            'c300_get_svc_info': '서비스 정보 조회 함수',
            'x000_mpfmoutq_proc': '출력 처리 수행 함수',
            'z000_norm_exit_proc': '프로그램 정상 종료 처리',
            'z999_err_exit_proc': '프로그램 에러 종료 처리'
        }
        
        found_functions = {}
        lines = content.splitlines()
        
        for i, line in enumerate(lines):
            for func_name, description in standard_functions.items():
                if func_name in line and ('(' in line or 'void' in line or 'int' in line):
                    found_functions[func_name] = {
                        'description': description,
                        'line_number': i + 1
                    }
        
        return {
            'standard_functions': standard_functions,
            'found_functions': found_functions
        }

    def get_c_file_context(self, file_path):
        """C 파일의 컨텍스트 정보를 반환"""
        if file_path in self.c_file_info:
            return self.c_file_info[file_path]
        return None

    def _analyze_sql_file_structure(self, content):
        """SQL 파일의 오라클 구조를 분석"""
        sql_features = {
            'hints': [],
            'bind_variables': [],
            'table_aliases': [],
            'outer_joins': [],
            'oracle_functions': [],
            'table_names': []
        }
        
        lines = content.splitlines()
        content_upper = content.upper()
        
        # 힌트 찾기 (/*+ ... */)
        import re
        hint_pattern = r'/\*\+([^*]+)\*/'
        hints = re.findall(hint_pattern, content)
        sql_features['hints'] = [hint.strip() for hint in hints]
        
        # 바인드 변수 찾기 (:variable)
        bind_pattern = r':(\w+)'
        binds = re.findall(bind_pattern, content)
        sql_features['bind_variables'] = list(set(binds))
        
        # 아우터 조인 찾기 ((+))
        if '(+)' in content:
            sql_features['outer_joins'] = ['Oracle outer join syntax detected']
        
        # 오라클 함수 찾기
        oracle_functions = ['NVL', 'TO_CHAR', 'SYSDATE', 'TO_DATE', 'DECODE', 'CASE']
        for func in oracle_functions:
            if func in content_upper:
                sql_features['oracle_functions'].append(func)
        
        # 유효성 체크 날짜 패턴 찾기
        validity_patterns = []
        if '99991231235959' in content:
            validity_patterns.append('99991231235959 (timestamp format)')
        if '99991231' in content:
            validity_patterns.append('99991231 (date format)')
        sql_features['validity_patterns'] = validity_patterns
        
        # 테이블 별칭 패턴 찾기 (단순한 방식으로)
        for line in lines:
            line_stripped = line.strip()
            if 'from' in line_stripped.lower() or 'join' in line_stripped.lower():
                # 간단한 별칭 패턴 매칭
                alias_pattern = r'(\w+)\s+(\w+)(?:\s|$|,)'
                matches = re.findall(alias_pattern, line_stripped, re.IGNORECASE)
                for match in matches:
                    if len(match[1]) <= 4:  # 짧은 별칭으로 가정
                        sql_features['table_aliases'].append(f"{match[0]} as {match[1]}")
        
        return sql_features

    def get_sql_file_context(self, file_path):
        """SQL 파일의 컨텍스트 정보를 반환"""
        if file_path in self.sql_file_info:
            return self.sql_file_info[file_path]
        return None
    
    def analyze_directory_structure(self, directory_path: str) -> dict:
        """디렉토리 구조 분석 결과를 반환"""
        return self.tree_analyzer.analyze_directory(directory_path)
    
    def suggest_files_for_query(self, directory_path: str, user_query: str) -> List[str]:
        """사용자 질문에 기반하여 관련 파일들을 추천"""
        return self.tree_analyzer.suggest_files_for_context(directory_path, user_query)
    
    def find_files_by_pattern(self, directory_path: str, pattern: str) -> List[str]:
        """패턴에 맞는 파일들을 찾기"""
        return self.tree_analyzer.find_files_by_pattern(directory_path, pattern)
    
    def _enhance_c_file_analysis(self, content: str, basic_analysis: Dict) -> Dict:
        """C 파일에 대한 향상된 분석"""
        enhanced = basic_analysis.copy()
        
        # 헤더 파일 include 분석 (섹션별로 분류)
        includes = self._categorize_includes(content)
        enhanced['includes'] = includes
        
        # IO 구조체 패턴 찾기
        io_patterns = {
            'input_structs': [],
            'output_structs': [],
            'context_structs': []
        }
        
        # Input/Output 구조체 찾기 (pio_*_in.h 패턴)
        all_includes = includes.get('io_formatter', []) + includes.get('static_library', []) + includes.get('other', [])
        for include in all_includes:
            if 'pio_' in include and '_in.h' in include:
                io_patterns['input_structs'].append(include)
            elif 'pio_' in include and '_out' in include:
                io_patterns['output_structs'].append(include)
        
        # Context 구조체 찾기
        ctx_pattern = r'typedef\s+struct\s+(\w*ctx\w*)\s+(\w+);'
        for match in re.finditer(ctx_pattern, content, re.IGNORECASE):
            io_patterns['context_structs'].append(match.group(2))
        
        enhanced['io_structures'] = io_patterns
        
        # DBIO 패턴 찾기
        enhanced['dbio_includes'] = includes.get('dbio_library', [])
        
        # Static Library 헤더들 (중요한 비즈니스 로직)
        enhanced['static_library_includes'] = includes.get('static_library', [])
        
        return enhanced
    
    def _categorize_includes(self, content: str) -> Dict[str, List[str]]:
        """헤더 파일들을 섹션별로 분류"""
        categories = {
            'system': [],           # 시스템 헤더 (<pfm*.h> 등)
            'io_formatter': [],     # IO Formatter 섹션
            'static_library': [],   # Static Library 섹션 (중요!)
            'dbio_library': [],     # DBIO Library 섹션
            'other': []
        }
        
        lines = content.split('\n')
        current_section = 'other'
        
        for line in lines:
            line = line.strip()
            
            # 섹션 감지
            if '--- IO Formatter   ---' in line or 'IO Formatter' in line:
                current_section = 'io_formatter'
                continue
            elif '--- Static Library ---' in line or 'Static Library' in line:
                current_section = 'static_library'
                continue
            elif '--- DBIO Library    ---' in line or 'DBIO Library' in line:
                current_section = 'dbio_library'
                continue
            
            # include 문 파싱
            include_match = re.match(r'#include\s*[<"](.*?)[>"]', line)
            if include_match:
                include_file = include_match.group(1)
                
                # 시스템 헤더 분류
                if include_file.startswith('pfm') or include_file.startswith('<'):
                    categories['system'].append(include_file)
                else:
                    categories[current_section].append(include_file)
        
        return categories
    
    def _analyze_header_file_structure(self, content: str, file_path: str = '') -> Dict:
        """헤더 파일 구조 분석"""
        analysis = {
            'type': 'unknown',
            'structures': [],
            'struct_details': {},
            'defines': [],
            'functions': []
        }
        
        # 구조체 정의와 내용 찾기
        struct_pattern = r'struct\s+(\w+)\s*\{([^}]*)\}'
        for match in re.finditer(struct_pattern, content, re.DOTALL):
            struct_name = match.group(1)
            struct_body = match.group(2)
            analysis['structures'].append(struct_name)
            analysis['struct_details'][struct_name] = self._parse_struct_fields(struct_body)
        
        # typedef 구조체 찾기
        typedef_pattern = r'typedef\s+struct\s+\w*\s*\{([^}]*)\}\s*(\w+);'
        for match in re.finditer(typedef_pattern, content, re.DOTALL):
            struct_body = match.group(1)
            struct_name = match.group(2)
            analysis['structures'].append(struct_name)
            analysis['struct_details'][struct_name] = self._parse_struct_fields(struct_body)
        
        # #define 찾기 (길이 정의도 포함)
        define_pattern = r'#define\s+(\w+)(?:\s+(.+?))?(?:\n|$)'
        for match in re.finditer(define_pattern, content):
            define_name = match.group(1)
            define_value = match.group(2).strip() if match.group(2) else ''
            analysis['defines'].append({
                'name': define_name,
                'value': define_value
            })
        
        # 헤더 파일 타입 결정 (파일명도 확인)
        if ('pio_' in content and ('_in' in content or '_out' in content)) or ('pio_' in file_path and ('_in.h' in file_path or '_out' in file_path)):
            analysis['type'] = 'io_structure'
        elif 'pdb_' in content or 'pdb_' in file_path:
            analysis['type'] = 'dbio_structure'
        elif any(func in content for func in ['void', 'int', 'long', 'char']):
            analysis['type'] = 'function_declarations'
        
        return analysis
    
    def _parse_struct_fields(self, struct_body: str) -> List[Dict]:
        """구조체 필드들을 파싱"""
        fields = []
        lines = struct_body.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('/*') or line.startswith('*') or line.startswith('//'):
                continue
            
            # 필드 패턴: type field_name[size]; /* comment */
            field_pattern = r'(\w+(?:\s*\*)?)\s+(\w+)(?:\s*\[([^\]]+)\])?\s*;(?:\s*/\*\s*(.+?)\s*\*/)?'
            match = re.match(field_pattern, line)
            
            if match:
                field_type = match.group(1).strip()
                field_name = match.group(2)
                field_size = match.group(3) if match.group(3) else None
                field_comment = match.group(4) if match.group(4) else ''
                
                fields.append({
                    'type': field_type,
                    'name': field_name,
                    'size': field_size,
                    'comment': field_comment
                })
        
        return fields
    
    def get_struct_info(self, file_path: str) -> Optional[Dict]:
        """특정 헤더 파일의 구조체 정보 반환"""
        if file_path not in self.files:
            return None
        
        content = self.files[file_path]
        return self._analyze_header_file_structure(content, file_path)
    
    def _analyze_xml_file_structure(self, content: str) -> Dict:
        """XML 파일 구조 분석 (UI 화면)"""
        analysis = {
            'form_id': '',
            'datasets': [],
            'ui_components': [],
            'functions': []
        }
        
        # Form ID 찾기
        form_id_pattern = r'FormID\(명\)\s*:\s*(\w+)'
        match = re.search(form_id_pattern, content)
        if match:
            analysis['form_id'] = match.group(1)
        
        # Dataset 찾기
        dataset_pattern = r'(d[sl]_\w+|DS_\w+)'
        datasets = set(re.findall(dataset_pattern, content, re.IGNORECASE))
        analysis['datasets'] = list(datasets)
        
        # UI 컴포넌트 찾기
        ui_components = []
        if 'gridView' in content:
            ui_components.append('gridView')
        if 'textbox' in content:
            ui_components.append('textbox')
        if 'input' in content:
            ui_components.append('input')
        if 'trigger' in content:
            ui_components.append('button')
        analysis['ui_components'] = ui_components
        
        # JavaScript 함수 찾기
        js_func_pattern = r'scwin\.(\w+)\s*='
        functions = set(re.findall(js_func_pattern, content))
        analysis['functions'] = list(functions)
        
        return analysis
