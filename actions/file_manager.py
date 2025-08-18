# actions/file_manager.py
import os

# 새로 추가: charset_normalizer로 인코딩 감지
try:
    from charset_normalizer import from_bytes
except ImportError:
    from_bytes = None

class FileManager:
    def __init__(self):
        self.files = {}
        self.c_file_info = {}  # C 파일의 구조 정보를 저장

    def add(self, file_paths):
        messages = []
        for file_path in file_paths:
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
                        self.c_file_info[file_path] = self._analyze_c_file_structure(content)
                        messages.append(
                            f"Read C file {file_path} with encoding {used_encoding} "
                            f"({line_count} lines, {char_count} chars) - Standard C structure detected"
                        )
                    else:
                        messages.append(
                            f"Read {file_path} with encoding {used_encoding} "
                            f"({line_count} lines, {char_count} chars)"
                        )
                except Exception as e:
                    messages.append(f"Error reading file {file_path}: {e}")
            else:
                # 새 파일의 경우 빈 문자열로 초기화
                self.files[file_path] = ""
                messages.append(f"Added new file (will be created on edit): {file_path}")
        return "\n".join(messages)

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
