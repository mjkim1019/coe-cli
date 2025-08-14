# CoE-CLI

CoE-CLI는 LLM 기반의 코드 편집 및 자동화를 위한 강력한 대화형 CLI 도구입니다. 사용자는 자연어 프롬프트와 슬래시(/) 명령어를 통해 파일을 편집하고, 셸 명령을 실행하며, 코드 변경 사항을 관리할 수 있습니다.

## 주요 기능

- **대화형 REPL 인터페이스**: 자연어 명령과 슬래시 명령어를 모두 지원하는 인터랙티브 세션을 제공합니다.
- **파일 경로 자동 완성**: `@` 문자를 입력하면 프로젝트 내 파일 목록이 자동으로 나타나 편리하게 파일을 선택할 수 있습니다.
- **안전한 파일 수정**: LLM이 제안한 변경 사항은 사용자 승인 전까지 실제 파일에 반영되지 않습니다. `diff`를 통해 변경 내용을 미리 확인할 수 있습니다.
- **세션 기반 파일 관리**: `/add`, `/drop` 명령어로 LLM이 편집할 파일을 유연하게 관리합니다.
- **셸 명령 실행**: `/run` 명령어로 테스트나 빌드 스크립트를 실행하고, 그 결과를 LLM의 컨텍스트로 활용할 수 있습니다.
- **변경 이력 관리**: `/diff`, `/undo` 명령어로 코드 변경 사항을 추적하고 이전 상태로 쉽게 되돌릴 수 있습니다.

## 아키텍처 레이어

```
+-------------------------------------------------+
|               Presentation Layer                |
|        (CLI Interface - prompt_toolkit)         |
+-------------------------------------------------+
|                Application Layer                |
| (Command Parser, Session/State, File Manager)   |
+-------------------------------------------------+
|                  Domain Layer                   |
|       (LLM Service, Diff Generator)             |
+-------------------------------------------------+
|               Infrastructure Layer              |
|       (File System, Shell Executor)             |
+-------------------------------------------------+
```

## 명령어

| 명령어 | 설명 | 사용 예시 |
| --- | --- | --- |
| `/add <files...>` | 편집할 파일을 세션에 추가합니다. 여러 파일을 동시에 추가할 수 있으며, 각 파일의 인코딩을 자동으로 감지합니다. | `/add @src/main.py @tests/test_main.py` (여러 파일을 입력할 때는 Tab 키로 자동 완성하고, spacebar 로 파일명을 구분하세요. Enter 를 치면 명령이 바로 실행됩니다.) |
| `/drop <files...>` | 세션에서 파일을 제거합니다. (실제 파일은 삭제되지 않음) | `/drop src/main.py` |
| `/diff` | LLM이 제안한 변경 사항이나 마지막 변경 내용의 `diff`를 확인합니다. | `/diff` |
| `/run <command>` | 셸 명령을 실행하고 결과를 출력합니다. | `/run pytest` |
| `/undo` | 마지막으로 적용된 변경 사항을 되돌립니다. | `/undo` |
| `/help` | 사용 가능한 모든 명령어와 설명을 보여줍니다. | `/help` |
| `/exit` | CLI를 종료합니다. | `/exit` |

## 설치

```bash
# pipx 설치 (없다면)
python3 -m pip install --user pipx
python3 -m pipx ensurepath
source ~/.zshrc  # PATH 반영

# Poetry 설치
pipx install poetry

# 프로젝트 의존성 설치
poetry install

# 방법 1) 가상환경 진입 후 실행
poetry env activate
coe-cli

# 방법 2) 바로 실행
poetry run coe-cli
```

## 사용법

```bash
coe-cli
```

터미널이 열리면 자유롭게 자연어 프롬프트를 입력하거나, `/help`를 입력하여 사용 가능한 명령어를 확인하세요.