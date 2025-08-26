# 🌀 Swing CLI 프로젝트

`Swing CLI`는 LLM 백엔드와 통신하여, 사용자가 코드에 대해 **질문하고**, **수정하고**, **테스트하며**, **코드 구조를 분석**할 수 있는 대화형 CLI 도구입니다.

## 프로젝트 구조

- `cli/` - CLI 인터페이스 관련 코드
  - `main.py` - 메인 CLI 애플리케이션
  - `completer.py` - 자동완성 기능
  - `core/` - 핵심 기능 모듈들
    - `context_manager.py` - 프롬프트 빌딩 관리
    - `ask_prompts.py` - ask 모드용 프롬프트
    - `edit_prompts.py` - edit 모드용 프롬프트
    - `base_prompts.py` - 기본 프롬프트
- `actions/` - 파일 및 명령 처리 액션
  - `file_manager.py` - 파일 관리 기능
  - `command_runner.py` - 명령 실행 기능
- `llm/` - LLM 서비스 연동
  - `service.py` - LLM API 통신 서비스
- `tests/` - 테스트 파일 및 픽스처

## 기술 스택

- **Language**: Python 3.8+
- **CLI Framework**: Click
- **Interactive Interface**: prompt_toolkit
- **LLM Integration**: OpenAI API
- **HTTP Client**: requests

## 주요 기능

1. **🧠 LLM 기반 코드 구조 분석** ✅: 계층 구조, 호출 관계, 파일 카테고리화, 자연어 요약 (`coe analyze` 명령어 구현 완료)
2. **💬 대화형 REPL** ✅: prompt_toolkit을 사용한 명령어 기반 인터페이스 및 자동완성
3. **🧩 파일 자동 인식** ✅: C 파일(.c)과 SQL 파일(.sql) 특화 분석 지원
4. **🔍 자동 분석** ✅: `/add` 및 `/edit` 시 LLM 기반 자동 분석 수행
5. **🧪 자동 테스트**: 파일 저장/수정 시 자동 테스트 실행 (Makefile, CMake 지원) - 개발 예정
6. **🧵 세션 관리**: 세션 저장/복구, LLM 기반 자동 컨텍스트 구성 - 개발 예정
7. **🧬 정교한 diff/patch**: 변경사항 분석, 패치 적용, 롤백, 자동 백업 - 개발 예정
8. **🧠 MCP (Multi-step Code Planning)**: LLM이 복잡한 요청을 단계별로 분해하여 실행 - 개발 예정
9. **🔐 권한 프롬프트**: LLM 호출, 실행 작업 등 사전 확인 시스템 - 개발 예정

## 실행 방법

1. 백엔드 서버 실행: `docker-compose up -d`
2. 가상환경 활성화: `source .venv/bin/activate`
3. 의존성 설치: `pip3 install -r requirements.txt`
4. CLI 실행: `python3 cli/main.py`

## 주요 명령어

### 현재 구현된 명령어
- `/add <파일>` - 파일을 컨텍스트에 추가
- `/ask` - 질문 모드
- `/edit` - 수정 모드 (whole/block/udiff 지원)
- `/test` - 테스트 실행
- `/preview` - 변경사항 미리보기
- `/apply` - 변경사항 적용
- `/help` - 도움말 표시
- `/exit` - CLI 종료

### 구현 완료 명령어
- `coe analyze` - 코드 구조 분석 (`python coe.py analyze <files>`) ✅
- `coe.py version` - 버전 정보 표시 ✅

### 개발 예정 명령어
- `coe test` - 테스트 실행
- `coe diff` - 변경점 확인
- `coe patch` - 수정 적용
- `coe revert` - 수정 롤백
- `coe save-session` - 세션 저장
- `coe resume` - 세션 복구
- `coe web` - Web UI 실행 (트리/그래프 시각화)

## 파일별 자동 인식 기능

### C 파일 (.c)
`/add` 명령으로 `.c` 확장자 파일이 추가될 때, 다음 표준 함수 구조를 자동으로 인식합니다:

- `a000_init_proc`: 프로그램 초기화 함수
- `b000_input_validation`: 입력 데이터 검증 수행
- `b999_output_setting`: 출력 전문의 순서 설정
- `c000_main_proc`: 실제 프로그램의 주요 로직 처리
- `c300_get_svc_info`: 서비스 정보 조회 함수
- `x000_mpfmoutq_proc`: 출력 처리 수행 함수
- `z000_norm_exit_proc`: 프로그램 정상 종료 처리
- `z999_err_exit_proc`: 프로그램 에러 종료 처리

### SQL 파일 (.sql)
`/add` 명령으로 `.sql` 확장자 파일이 추가될 때, 다음 Oracle SQL 특징들을 자동으로 분석합니다:

- **오라클 힌트**: `/*+ index(...) use_nl(...) */` 등의 성능 최적화 힌트
- **바인드 변수**: `:svc_mgmt_num`, `:bas_dt` 등의 파라미터
- **아우터 조인**: Oracle 전용 `(+)` 구문
- **오라클 함수**: NVL, TO_CHAR, SYSDATE 등
- **테이블 별칭**: zs, zatr, zssy 등의 축약 별칭
- **유효성 체크**: `99991231235959` 또는 `99991231`을 사용한 무한대 날짜 패턴

이러한 구조 정보들은 LLM이 각 파일의 특성을 정확히 이해할 수 있도록 컨텍스트에 자동으로 포함됩니다.

## 특수 용어 인식

### DBIO (Database Input/Output)
사용자가 "dbio"에 대해 질문할 때 자동으로 데이터베이스 입출력 관련 컨텍스트로 인식합니다:
- SQL 쿼리 작성 및 최적화
- 데이터베이스 연결 및 트랜잭션 처리
- 데이터 입출력 로직 분석
- 성능 튜닝 관련 질문

## 개발 가이드

이 프로젝트를 수정할 때는:
- Python 코딩 스타일을 일관되게 유지
- prompt_toolkit과 click 라이브러리 사용 패턴 준수
- 모듈화된 구조 유지 (cli, actions, llm 모듈 분리)
- 한국어 사용자 친화적 메시지 제공
- C 파일 추가 시 표준 함수 구조 정보를 자동으로 컨텍스트에 포함
- SQL 파일 추가 시 Oracle SQL 특징을 자동으로 분석하여 컨텍스트에 포함