# Swing CLI 프로젝트

`Swing CLI`는 LLM 백엔드와 통신하여, 사용자가 코드에 대해 **질문하고**, **수정하고**, **테스트하며**, **코드 구조를 분석**할 수 있는 대화형 CLI 도구입니다.

## 빠른 시작

### 실행 방법

```bash
python3 cli/main.py
```

### 주요 명령어

- `/add <파일>` - 파일을 컨텍스트에 추가
- `/ask` - 질문 모드
- `/edit` - 수정 모드 (whole/block/udiff 지원)
- `/test` - 테스트 실행
- `/preview` - 변경사항 미리보기
- `/apply` - 변경사항 적용
- `/repo` - 리포지토리 맵 생성
- `/help` - 도움말 표시
- `/exit` - CLI 종료

## 프로젝트 구조

- `cli/` - CLI 인터페이스 관련 코드
  - `main.py` - 메인 CLI 애플리케이션
  - `completer.py` - 자동완성 기능
  - `core/` - 핵심 기능 모듈들
    - `context_manager.py` - 프롬프트 빌딩 관리 (ASK 모드 백그라운드 분석 포함)
    - `analyzer.py` - CoeAnalyzer 코드 구조 분석 엔진
    - `ask_prompts.py` - ask 모드용 프롬프트
    - `edit_prompts.py` - edit 모드용 프롬프트
    - `base_prompts.py` - 기본 프롬프트
- `actions/` - 파일 및 명령 처리 액션
  - `file_manager.py` - 파일 관리 기능
  - `command_runner.py` - 명령 실행 기능
- `llm/` - LLM 서비스 연동
  - `service.py` - LLM API 통신 서비스
- `prompts/` - 파일 타입별 특화 분석 프롬프트
  - `c_file_prompt.py` - C 파일 전용 분석 프롬프트
  - `xml_file_prompt.py` - XML 파일 전용 분석 프롬프트
  - `sql_file_prompt.py` - SQL 파일 전용 분석 프롬프트
  - `generic_file_prompt.py` - 일반 파일 기본 프롬프트
- `tests/` - 테스트 파일 및 픽스처

## 기술 스택

- **Language**: Python 3.8+
- **CLI Framework**: Click
- **Interactive Interface**: prompt_toolkit
- **LLM Integration**: OpenAI API
- **HTTP Client**: requests

## 아키텍처

`coe-cli`는 사용자의 입력을 받아 백엔드 서버로 전달하는 **클라이언트**와, 실제 LLM 호출을 처리하는 **백엔드**로 구성된 클라이언트-서버 아키텍처를 따릅니다. 원활한 사용을 위해 백엔드 서버가 먼저 실행되어야 합니다.

## 개발 가이드

이 프로젝트를 수정할 때는:
- Python 코딩 스타일을 일관되게 유지
- prompt_toolkit과 click 라이브러리 사용 패턴 준수
- 모듈화된 구조 유지 (cli, actions, llm, prompts 모듈 분리)
- 한국어 사용자 친화적 메시지 제공
- **파일 타입별 특화 분석**: 파일 확장자에 따라 적절한 전용 프롬프트 사용
- **nullable 정보 필수**: 모든 입출력 파라미터에 nullable 여부 포함
- **디버그 로그 유지**: LLM 분석 과정의 투명성을 위해 디버그 정보 출력
- **Rich 테이블 형식**: 분석 결과를 보기 좋은 표 형태로 출력

## 문서

- [제품 요구사항](swing_cli_prd.md) - 제품 개요, 목표, 성공 지표
- [기능 명세서](docs/features_spec.md) - 상세 기능 설명 및 구현 계획