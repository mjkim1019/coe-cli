# Mider

`Mider`는 LLM 기반 대화형 코드 분석 및 편집 CLI 도구입니다. 코드에 대해 **질문하고**, **수정하고**, **구조를 분석**할 수 있습니다.

## 빠른 시작

```bash
# 실행
python3 run.py

# 또는
python3 cli/main.py
```

## 주요 기능

| 기능 | 설명 |
|------|------|
| **Ask 모드** | 코드에 대해 자연어로 질문 |
| **Edit 모드** | 3가지 전략으로 코드 수정 (wholefile/editblock/udiff) |
| **Architect 모드** | AI가 복잡한 작업을 단계별 계획으로 분해 실행 |
| **파일타입 분석** | C, SQL, XML 파일 전용 분석 프롬프트 |
| **Tutorial 모드** | 처음 사용자를 위한 대화형 가이드 |

## 명령어

### 기본 명령어
| 명령어 | 설명 |
|--------|------|
| `/add <파일>` | 파일을 컨텍스트에 추가 |
| `/files` | 추가된 파일 목록 보기 |
| `/tree` | 파일 트리 구조 보기 |
| `/info <파일>` | 파일 상세 분석 정보 |
| `/clear` | 대화 기록 초기화 |

### 모드 전환
| 명령어 | 설명 |
|--------|------|
| `/ask` | 질문/분석 모드 |
| `/edit [전략]` | 수정 모드 (wholefile/editblock/udiff) |
| `/architect` | AI 작업 오케스트레이션 모드 |
| `/tutorial` | 대화형 튜토리얼 |

### 편집 관련
| 명령어 | 설명 |
|--------|------|
| `/preview` | 변경사항 미리보기 |
| `/apply` | 변경사항 적용 |
| `/history` | 편집 히스토리 |
| `/rollback <ID>` | 편집 롤백 |

### 분석 도구
| 명령어 | 설명 |
|--------|------|
| `/repo [파일들]` | Repository Map 생성 |
| `/mider-cache` | MiderAnalyzer 캐시 상태 |

## 프로젝트 구조

```
mider/
├── run.py                      # 진입점
│
├── cli/                        # CLI 애플리케이션
│   ├── main.py                 # 메인 REPL 루프
│   ├── completer.py            # 자동완성
│   │
│   ├── core/                   # 핵심 로직
│   │   ├── analyzer.py         # MiderAnalyzer (코드 분석 엔진)
│   │   ├── context_manager.py  # 프롬프트 빌딩 및 캐싱
│   │   ├── debug_manager.py    # 디버그 출력 관리
│   │   ├── mcp_integration.py  # MCP 프로토콜 통합
│   │   ├── ask_prompts.py      # Ask 모드 프롬프트
│   │   └── edit_prompts.py     # Edit 모드 프롬프트
│   │
│   ├── architect/              # AI 작업 오케스트레이션
│   │   ├── mode.py             # Architect 모드 로직
│   │   ├── plan.py             # 실행 계획 데이터 구조
│   │   └── prompts.py          # Architect 프롬프트
│   │
│   ├── coders/                 # 편집 전략 (Aider 영감)
│   │   ├── base_coder.py       # 기본 클래스 및 레지스트리
│   │   ├── wholefile_coder.py  # 전체 파일 교체 전략
│   │   ├── editblock_coder.py  # 블록 교체 전략
│   │   ├── udiff_coder.py      # Unified Diff 전략
│   │   └── repo_mapper.py      # Repository 매핑
│   │
│   └── ui/                     # UI 컴포넌트
│       ├── components.py       # Rich UI 요소
│       ├── panels.py           # UI 패널
│       ├── formatters.py       # 응답 포매팅
│       ├── interactive.py      # 대화형 UI 헬퍼
│       └── tutorial.py         # 튜토리얼 모드
│
├── actions/                    # 파일 작업
│   ├── file_manager.py         # 파일 컨텍스트 관리
│   ├── file_editor.py          # 파일 편집 및 백업/롤백
│   ├── file_tree_analyzer.py   # 파일 트리 분석
│   ├── template_manager.py     # 템플릿 관리
│   └── document_generator.py   # 문서 생성
│
├── llm/                        # LLM 통합
│   └── service.py              # LLM API 클라이언트
│
├── mcp/                        # MCP 프로토콜
│   ├── client.py               # MCP HTTP 클라이언트
│   └── tools.py                # MCP 도구 관리
│
└── prompts/                    # 파일타입별 분석 프롬프트
    ├── c_file_prompt.py        # C 파일 분석
    ├── sql_file_prompt.py      # SQL 파일 분석
    ├── xml_file_prompt.py      # XML 파일 분석
    └── generic_file_prompt.py  # 일반 파일 분석
```

## 기술 스택

- **Language**: Python 3.8+
- **CLI Framework**: Click
- **Interactive Interface**: prompt_toolkit
- **LLM Integration**: OpenAI API
- **UI**: Rich library
- **HTTP Client**: requests

## 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                         CLI Layer                            │
│  ┌─────────┐  ┌──────────┐  ┌───────────┐  ┌────────────┐  │
│  │  main   │  │ completer│  │    ui/    │  │  architect │  │
│  └────┬────┘  └──────────┘  └───────────┘  └────────────┘  │
│       │                                                      │
│  ┌────┴────────────────────────────────────────────────┐    │
│  │                    core/                             │    │
│  │  analyzer, context_manager, debug_manager, prompts  │    │
│  └────┬────────────────────────────────────────────────┘    │
│       │                                                      │
│  ┌────┴────┐  ┌──────────┐                                  │
│  │ coders/ │  │  mcp/    │                                  │
│  └─────────┘  └──────────┘                                  │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────┴─────────────────────────────────────┐
│                     Service Layer                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │   actions/   │  │    llm/      │  │    prompts/      │   │
│  │ file_manager │  │   service    │  │ c/sql/xml/generic│   │
│  │ file_editor  │  └──────────────┘  └──────────────────┘   │
│  └──────────────┘                                            │
└─────────────────────────────────────────────────────────────┘
```

## 문서

- [기능 명세서](docs/features_spec.md)
- [개발 컨벤션](docs/development_convention.md)
- [사용 가이드](docs/MIDER_USAGE.md)
- [제품 요구사항](docs/mider_prd.md)
