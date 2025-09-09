#!/usr/bin/env python3
"""
Swing CLI 실행 스크립트
환경변수를 로드한 후 메인 CLI를 실행합니다.
"""

import os
import sys
from pathlib import Path

# 프로젝트 루트 디렉토리 설정
PROJECT_ROOT = Path(__file__).parent

# 가상환경 경로 추가 (가상환경이 활성화되지 않은 경우를 위해)
venv_path = PROJECT_ROOT / '.venv' / 'lib' / 'python3.13' / 'site-packages'
if venv_path.exists():
    sys.path.insert(0, str(venv_path))

# .env 파일 로드
try:
    from dotenv import load_dotenv
    env_file = PROJECT_ROOT / '.env'
    if env_file.exists():
        load_dotenv(env_file)
        print(f"✅ 환경변수 로드됨: {env_file}")
    else:
        print(f"⚠️  .env 파일을 찾을 수 없습니다: {env_file}")
except ImportError:
    print("❌ python-dotenv를 찾을 수 없습니다.")
    print("해결방법: source .venv/bin/activate 후 실행하거나")
    print("         .venv/bin/python run.py 로 실행하세요")
    sys.exit(1)

# Python path 설정
sys.path.insert(0, str(PROJECT_ROOT))

# CLI 모듈 실행
if __name__ == '__main__':
    from cli.main import main
    main()