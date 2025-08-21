# actions/file_tree_analyzer.py
import os
import fnmatch
from typing import Dict, List, Set, Tuple, Optional

class FileTreeAnalyzer:
    """파일 트리를 분석하고 필요한 파일을 찾는 클래스"""
    
    def __init__(self):
        # 제외할 디렉토리/파일 패턴
        self.exclude_patterns = [
            '.git', '.git/*',
            '__pycache__', '__pycache__/*', '*.pyc', '*.pyo',
            'node_modules', 'node_modules/*',
            '.venv', '.venv/*', 'venv', 'venv/*',
            '.pytest_cache', '.pytest_cache/*',
            'dist', 'dist/*', 'build', 'build/*',
            '*.log', '*.tmp', '*.temp',
            '.DS_Store', 'Thumbs.db',
            '*.egg-info', '*.egg-info/*'
        ]
        
        # 주요 파일 확장자 정의 (프로젝트 특성에 맞게)
        self.primary_extensions = ['.c', '.h', '.sql', '.xml', '.js', '.tar']
        
        # 파일 타입별 분석 패턴
        self.file_patterns = {
            'c_files': {
                'extensions': ['.c'],
                'functions': [
                    'a000_init_proc', 'b000_input_validation', 'b999_output_setting',
                    'c000_main_proc', 'c300_get_svc_info', 'x000_mpfmoutq_proc',
                    'z000_norm_exit_proc', 'z999_err_exit_proc'
                ]
            },
            'header_files': {
                'extensions': ['.h'],
                'patterns': ['pio_', '_in.h', '_out.h', 'pdb_']
            },
            'sql_files': {
                'extensions': ['.sql'],
                'oracle_features': ['/*+', ':bind_var', '(+)', 'NVL', 'TO_CHAR', 'SYSDATE', '99991231']
            },
            'xml_files': {
                'extensions': ['.xml', '.XML'],
                'ui_patterns': ['scwin.', 'form_onLoadCompleted', 'gridView', 'dataset']
            },
            'js_files': {
                'extensions': ['.js'],
                'web_patterns': ['function', 'var ', 'console.log', 'ngmf.']
            },
            'archive_files': {
                'extensions': ['.tar', '.zip', '.gz']
            }
        }
    
    def analyze_directory(self, directory_path: str, max_depth: int = 3) -> Dict:
        """디렉토리를 분석하여 구조 정보를 반환"""
        if not os.path.isdir(directory_path):
            return {'error': f'Directory not found: {directory_path}'}
        
        analysis = {
            'path': directory_path,
            'structure': {},
            'file_categories': {},
            'project_insights': {},
            'suggested_files': [],
            'total_files': 0
        }
        
        # 재귀적으로 디렉토리 구조 분석
        structure, file_count = self._scan_directory(directory_path, max_depth, 0)
        analysis['structure'] = structure
        analysis['total_files'] = file_count
        
        # 파일 카테고리별 분류
        analysis['file_categories'] = self._categorize_files(structure, directory_path)
        
        # 프로젝트 인사이트 생성
        analysis['project_insights'] = self._analyze_project_type(analysis['file_categories'])
        
        # 컨텍스트 추가 추천 파일들
        analysis['suggested_files'] = self._suggest_context_files(analysis['file_categories'])
        
        return analysis
    
    def _scan_directory(self, path: str, max_depth: int, current_depth: int) -> Tuple[Dict, int]:
        """재귀적으로 디렉토리를 스캔"""
        if current_depth >= max_depth:
            return {'...': f'max_depth({max_depth})_reached'}, 0
        
        structure = {}
        total_files = 0
        
        try:
            items = sorted(os.listdir(path))
        except (PermissionError, OSError):
            return {'permission_denied': True}, 0
        
        for item in items:
            item_path = os.path.join(path, item)
            
            # 제외 패턴 확인
            if self._should_exclude(item, item_path):
                continue
            
            if os.path.isdir(item_path):
                sub_structure, sub_count = self._scan_directory(item_path, max_depth, current_depth + 1)
                if sub_structure:  # 빈 디렉토리가 아닌 경우만 추가
                    structure[f"{item}/"] = sub_structure
                    total_files += sub_count
            else:
                # 파일 정보 저장
                try:
                    file_info = {
                        'size': os.path.getsize(item_path),
                        'extension': os.path.splitext(item)[1].lower(),
                        'is_primary': os.path.splitext(item)[1].lower() in self.primary_extensions
                    }
                    structure[item] = file_info
                    total_files += 1
                except OSError:
                    continue
        
        return structure, total_files
    
    def _should_exclude(self, item_name: str, item_path: str) -> bool:
        """파일/디렉토리가 제외 대상인지 확인"""
        for pattern in self.exclude_patterns:
            if fnmatch.fnmatch(item_name, pattern) or fnmatch.fnmatch(item_path, pattern):
                return True
        return False
    
    def _categorize_files(self, structure: Dict, base_path: str, prefix: str = "") -> Dict[str, List[Dict]]:
        """파일들을 타입별로 분류하고 상세 정보 포함"""
        categories = {
            'c_files': [],
            'header_files': [],
            'sql_files': [],
            'xml_files': [],
            'js_files': [],
            'archive_files': [],
            'other_files': []
        }
        
        for name, info in structure.items():
            full_path = os.path.join(prefix, name) if prefix else name
            
            if isinstance(info, dict):
                if name.endswith('/'):
                    # 디렉토리인 경우 재귀적으로 처리
                    sub_categories = self._categorize_files(info, base_path, full_path)
                    for cat, files in sub_categories.items():
                        categories[cat].extend(files)
                else:
                    # 파일인 경우 카테고리 분류
                    ext = info.get('extension', '')
                    category = self._get_file_category(ext)
                    
                    file_entry = {
                        'path': full_path,
                        'full_path': os.path.join(base_path, full_path),
                        'size': info.get('size', 0),
                        'extension': ext,
                        'is_primary': info.get('is_primary', False)
                    }
                    
                    # 파일 내용 기반 추가 분석 (주요 파일들만)
                    if info.get('is_primary', False):
                        file_entry['analysis'] = self._analyze_file_content(file_entry['full_path'], category)
                    
                    categories[category].append(file_entry)
        
        return categories
    
    def _get_file_category(self, extension: str) -> str:
        """파일 확장자를 기반으로 카테고리 결정"""
        for category, config in self.file_patterns.items():
            if extension in config['extensions']:
                return category
        return 'other_files'
    
    def _analyze_file_content(self, file_path: str, category: str) -> Optional[Dict]:
        """파일 내용을 분석하여 추가 정보 제공"""
        if not os.path.exists(file_path):
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(2000)  # 처음 2000자만 분석
        except Exception:
            return None
        
        analysis = {}
        
        if category == 'c_files':
            # C 파일 함수 분석
            found_functions = []
            for func in self.file_patterns['c_files']['functions']:
                if func in content:
                    found_functions.append(func)
            analysis['standard_functions'] = found_functions
            
            # include 분석
            includes = []
            for line in content.split('\n')[:50]:  # 처음 50줄만
                if line.strip().startswith('#include'):
                    includes.append(line.strip())
            analysis['includes'] = includes
        
        elif category == 'sql_files':
            # SQL 오라클 특징 분석
            oracle_features = []
            for feature in self.file_patterns['sql_files']['oracle_features']:
                if feature in content:
                    oracle_features.append(feature)
            analysis['oracle_features'] = oracle_features
            
            # 바인드 변수 추출
            import re
            bind_vars = re.findall(r':(\w+)', content)
            analysis['bind_variables'] = list(set(bind_vars))[:10]  # 최대 10개
        
        elif category == 'xml_files':
            # XML UI 패턴 분석
            ui_patterns = []
            for pattern in self.file_patterns['xml_files']['ui_patterns']:
                if pattern in content:
                    ui_patterns.append(pattern)
            analysis['ui_patterns'] = ui_patterns
        
        return analysis
    
    def _analyze_project_type(self, file_categories: Dict) -> Dict:
        """파일 분석을 기반으로 프로젝트 타입 및 특징 분석"""
        insights = {
            'project_type': 'unknown',
            'characteristics': [],
            'tech_stack': [],
            'complexity': 'low'
        }
        
        c_count = len(file_categories.get('c_files', []))
        h_count = len(file_categories.get('header_files', []))
        sql_count = len(file_categories.get('sql_files', []))
        xml_count = len(file_categories.get('xml_files', []))
        
        # 프로젝트 타입 결정
        if c_count > 0 and h_count > 0:
            insights['project_type'] = 'enterprise_c_system'
            insights['characteristics'].append('C 기반 엔터프라이즈 시스템')
            insights['tech_stack'].extend(['C', 'Oracle DB'])
        
        if sql_count > 0:
            insights['characteristics'].append('데이터베이스 집약적')
            insights['tech_stack'].append('SQL/Oracle')
        
        if xml_count > 0:
            insights['characteristics'].append('웹 UI 포함')
            insights['tech_stack'].append('Web UI')
        
        # 복잡도 평가
        total_primary_files = c_count + h_count + sql_count + xml_count
        if total_primary_files > 20:
            insights['complexity'] = 'high'
        elif total_primary_files > 10:
            insights['complexity'] = 'medium'
        
        return insights
    
    def _suggest_context_files(self, file_categories: Dict) -> List[Dict]:
        """컨텍스트에 추가하면 좋을 파일들 추천"""
        suggestions = []
        
        # C 파일 관련 추천
        c_files = file_categories.get('c_files', [])
        if c_files:
            # 메인 로직이 있는 C 파일 우선 추천
            for c_file in c_files:
                analysis = c_file.get('analysis', {})
                functions = analysis.get('standard_functions', [])
                if 'c000_main_proc' in functions or 'a000_init_proc' in functions:
                    suggestions.append({
                        'file': c_file['path'],
                        'reason': '메인 로직 포함',
                        'priority': 'high'
                    })
        
        # 헤더 파일 중 입출력 구조체 추천
        header_files = file_categories.get('header_files', [])
        for h_file in header_files:
            if any(pattern in h_file['path'] for pattern in ['_in.h', '_out.h', 'pio_']):
                suggestions.append({
                    'file': h_file['path'],
                    'reason': '입출력 구조체 정의',
                    'priority': 'medium'
                })
        
        # SQL 파일 추천 (DBIO 관련)
        sql_files = file_categories.get('sql_files', [])
        for sql_file in sql_files:
            suggestions.append({
                'file': sql_file['path'],
                'reason': '데이터베이스 로직',
                'priority': 'medium'
            })
        
        return suggestions[:10]  # 최대 10개 추천
    
    def find_files_by_pattern(self, directory: str, pattern: str, recursive: bool = True) -> List[str]:
        """패턴에 맞는 파일들을 찾기"""
        found_files = []
        
        if recursive:
            for root, dirs, files in os.walk(directory):
                # 제외할 디렉토리들 필터링
                dirs[:] = [d for d in dirs if not self._should_exclude(d, os.path.join(root, d))]
                
                for file in files:
                    file_path = os.path.join(root, file)
                    if not self._should_exclude(file, file_path) and fnmatch.fnmatch(file, pattern):
                        found_files.append(file_path)
        else:
            try:
                for item in os.listdir(directory):
                    item_path = os.path.join(directory, item)
                    if os.path.isfile(item_path) and not self._should_exclude(item, item_path) and fnmatch.fnmatch(item, pattern):
                        found_files.append(item_path)
            except (PermissionError, OSError):
                pass
        
        return sorted(found_files)
    
    def suggest_files_for_context(self, directory: str, user_query: str) -> List[str]:
        """사용자 질문을 기반으로 컨텍스트에 추가할 파일들을 추천"""
        analysis = self.analyze_directory(directory)
        suggestions = []
        
        # 질문 키워드 분석
        query_lower = user_query.lower()
        keywords = {
            'main': ['main', 'entry', '시작', '메인', 'c000_main_proc'],
            'dbio': ['dbio', 'database', 'sql', 'db', '데이터베이스', 'select', 'insert'],
            'ui': ['ui', 'xml', 'screen', 'form', '화면', '폼'],
            'header': ['header', 'struct', '구조체', 'in.h', 'out.h'],
            'init': ['init', '초기화', 'a000_init_proc'],
            'error': ['error', 'err', '에러', 'z999_err_exit_proc']
        }
        
        detected_categories = []
        for category, terms in keywords.items():
            if any(term in query_lower for term in terms):
                detected_categories.append(category)
        
        # 카테고리별 파일 추천
        file_categories = analysis.get('file_categories', {})
        
        if 'main' in detected_categories:
            # 메인 로직 파일들 추천
            for c_file in file_categories.get('c_files', []):
                analysis_info = c_file.get('analysis', {})
                if 'c000_main_proc' in analysis_info.get('standard_functions', []):
                    suggestions.append(c_file['full_path'])
        
        if 'dbio' in detected_categories:
            # SQL 파일들과 DB 관련 헤더 파일들 추가
            for sql_file in file_categories.get('sql_files', []):
                suggestions.append(sql_file['full_path'])
            # DB 관련 헤더 파일들도 찾기
            for h_file in file_categories.get('header_files', []):
                if 'pdb_' in h_file['path']:
                    suggestions.append(h_file['full_path'])
        
        if 'ui' in detected_categories:
            # XML 파일들 추가
            for xml_file in file_categories.get('xml_files', []):
                suggestions.append(xml_file['full_path'])
        
        if 'header' in detected_categories:
            # 입출력 헤더 파일들 추가
            for h_file in file_categories.get('header_files', []):
                if any(pattern in h_file['path'] for pattern in ['_in.h', '_out.h', 'pio_']):
                    suggestions.append(h_file['full_path'])
        
        # 중복 제거 및 존재하는 파일들만 반환
        unique_suggestions = []
        for file_path in suggestions:
            if os.path.exists(file_path) and file_path not in unique_suggestions:
                unique_suggestions.append(file_path)
        
        return unique_suggestions[:10]  # 최대 10개까지만 추천