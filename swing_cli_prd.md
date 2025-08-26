
# 🌀 Product Requirements Document (PRD)

## 🧰 Product Name: `Swing CLI`

## 🧑‍💻 Target Users
- 개발자 (Python, C, SQL 등 사용하는 팀)
- 프로그램 운영자 (시스템 분석, 유지보수, 배포 전 검토 등)

---

## 🎯 Objective
`Swing CLI`는 LLM 백엔드와 통신하여, 사용자가 코드에 대해 **질문하고**, **수정하고**, **테스트하며**, **코드 구조를 분석**할 수 있는 대화형 CLI 도구입니다.  
CLI 중심의 워크플로우에서 다음과 같은 기능을 제공합니다:

- 코드 구조 파악 (계층 구조, 호출 관계, in/out 등)
- 대화형 질문 및 수정
- 자동 테스트
- LLM 기반 요약 및 리팩토링 지원
- 세션 저장, diff/patch, 충돌 복구 등 편의 기능

---

## 📁 프로젝트 구조

```
swing-cli/
├── cli/
│   ├── main.py
│   ├── completer.py
│   └── core/
│       ├── context_manager.py
│       ├── ask_prompts.py
│       ├── edit_prompts.py
│       └── base_prompts.py
├── actions/
│   ├── file_manager.py
│   └── command_runner.py
├── llm/
│   └── service.py
├── tests/
└── .coe/
```

---

## 🔧 기술 스택

| 항목 | 내용 |
|------|------|
| 언어 | Python 3.8+ |
| CLI 프레임워크 | Click |
| 대화형 UI | prompt_toolkit |
| LLM 연동 | OpenAI API |
| HTTP | requests |
| C 테스트 | Makefile, CMake, gcc |
| 시각화 | HTML/JS (트리, 그래프) |

---

## 🔑 주요 기능

### 1. 🧠 LLM 기반 코드 구조 분석 (`coe analyze`) ✅ 구현 완료

| 항목 | 설명 | 구현 상태 |
|------|------|----------|
| 계층 구조 | 디렉토리-파일-함수 구조 트리 | ✅ 완료 |
| 호출 관계 | 함수 간 call graph | ✅ 완료 |
| in/out 정보 | 함수별 input/output 파라미터 추론 | ✅ 완료 |
| 파일 요약 | 자연어 요약 (주석/내용 기반) | ✅ 완료 |
| 파일 카테고리화 | `controller`, `utils`, `service`, `sql`, `config` 등 | ✅ 완료 |
| 출력 | CLI(Markdown) + Web UI (트리/그래프 시각화) | ✅ CLI 완료, Web UI 예정 |
| 자동 분석 | `/add` 및 `/edit` 시 자동 LLM 분석 수행 | ✅ 완료 |
| 독립 실행 | `python coe.py analyze <files>` 명령어 지원 | ✅ 완료 |

---

### 2. 💬 대화형 CLI REPL

- 명령어 기반 대화형 인터페이스
- 명령어 자동완성 지원
- `/add <파일>`로 작업 컨텍스트에 파일 추가
- `/ask`, `/edit` 명령으로 모드 전환
- 한국어 질문 지원

---

### 3. 🧩 파일 자동 인식 및 구조 파악

#### 🟦 C 파일 (.c)
- 표준 함수 패턴 자동 인식:
  - `a000_init_proc`, `b000_input_validation`, ...
  - `z999_err_exit_proc`

#### 🟨 SQL 파일 (.sql)
- Oracle SQL 특화 분석:
  - 힌트, 바인드 변수, 아우터 조인, 날짜 패턴, 별칭 등 자동 감지

---

### 4. 🧪 테스트 기능

| 기능 | 설명 |
|------|------|
| 자동 실행 | 파일 저장/수정 시 자동 테스트 |
| 수동 실행 | `coe test`, `coe test <file>` |
| 실행 방식 | Makefile, CMake 또는 내장 스크립트 |
| 출력 | ✅ 성공 여부 + ❌ 에러, 로그, diff 포함 |

---

### 5. 🧵 세션 및 컨텍스트 관리

| 기능 | 설명 |
|------|------|
| 세션 저장 | `coe save-session` |
| 세션 불러오기 | `coe resume` |
| 컨텍스트 구성 | `/add` 또는 LLM 요청 승인 기반 |

---

### 6. 🔐 권한 프롬프트 및 스킵

| 기능 | 설명 |
|------|------|
| 승인 요청 | LLM 호출, 실행 작업 등 사전 확인 |
| 플래그 사용 | `--yes`, `--skip-confirmation` |

---

### 7. 🧠 LLM ReAct 루프 + 도구 호출

| 기능 | 설명 |
|------|------|
| ReAct | 추론 + 도구 호출 반복 |
| 예시 도구 | `get_file_tree()`, `summarize()`, `find_calls()` |
| 목적 | 정확한 구조 분석, 리팩토링 |

---

### 8. 🧬 정교한 diff 및 충돌 복구

| 기능 | 설명 |
|------|------|
| 변경 diff | `coe diff` |
| 패치 적용 | `coe patch` |
| 롤백 | `coe revert` |
| 백업 | `.bak`, `.diff` 자동 생성 |

---

### 9. 🧠 MCP (Multi-step Code Planning)

| 기능 | 설명 |
|------|------|
| 계획 생성 | LLM이 사용자 요청을 multi-step 변경 작업으로 분해 |
| 자동 실행 | 변경 계획 단위로 적용 (`plan`, `step`, `verify`) |
| 예시 | "로깅 추가" → [1. 모듈 import, 2. 로그 함수 삽입, 3. 테스트 수행] |
| 상태 저장 | 각 step 별 상태 기억 및 rollback 가능 |

---

## 📊 CLI 명령어 요약

| 명령어 | 설명 |
|--------|------|
| `/add <파일>` | 파일 컨텍스트에 추가 |
| `/ask` | 질문 모드 |
| `/edit` | 수정 모드 |
| `/test` | 테스트 실행 |
| `coe analyze` | 구조 분석 |
| `coe diff` | 변경점 확인 |
| `coe patch` | 수정 적용 |
| `coe revert` | 수정 롤백 |
| `coe save-session` | 세션 저장 |
| `coe resume` | 세션 복구 |
| `coe web` | Web UI 실행 |

---

## 📅 Release Plan

| 버전 | 기능 | 상태 |
|------|------|------|
| v0.1 | 기본 CLI + 파일 관리 | ✅ 완료 |
| v0.2 | 구조 분석 + 테스트 | ✅ 완료 (`coe analyze` 명령어 구현) |
| v0.3 | Web 시각화 + MCP + ReAct | ⏳ 진행 중 |
| v0.4 | 세션 관리, diff 복구 등 | 📌 예정 |

---

## ✅ Non-Functional Requirements

| 항목 | 요구사항 |
|------|----------|
| 퍼포먼스 | 대용량 코드도 5초 이내 응답 |
| 안정성 | 실패 시 fallback 처리 |
| 확장성 | 다언어 분석 가능 구조 |
| UX | 한국어 메시지 및 자동완성 지원 |
| 보안 | 외부 전송 전 사용자 승인 필수 |
