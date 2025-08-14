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
