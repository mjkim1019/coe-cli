# Swing CLI 프로젝트

`Swing CLI`는 LLM 백엔드와 통신하여, 사용자가 코드에 대해 **질문하고**, **수정하고**, **테스트하며**, **코드 구조를 분석**할 수 있는 대화형 CLI 도구입니다.

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
- `prompts/` - 파일 타입별 특화 분석 프롬프트 ✅
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

## 주요 기능

1. **🧠 LLM 기반 코드 구조 분석** ✅: 계층 구조, 호출 관계, 파일 카테고리화, 자연어 요약
2. **💬 대화형 REPL** ✅: prompt_toolkit을 사용한 명령어 기반 인터페이스 및 자동완성
3. **🧩 파일 타입별 특화 분석** ✅: C 파일(.c), XML 파일(.xml), SQL 파일(.sql) 전용 프롬프트 지원
4. **🔍 자동 분석** ✅: `/add` 시 기본 분석 + LLM 기반 심화 분석, `/ask` 시 백그라운드 구조 분석
5. **📊 JSON 응답 처리** ✅: ```json 형태 LLM 응답을 자동으로 테이블로 변환하여 표시
6. **🐛 디버그 정보** ✅: LLM 호출 과정의 투명성을 위한 상세 디버그 출력
7. **🧪 자동 테스트**: 파일 저장/수정 시 자동 테스트 실행 (Makefile, CMake 지원) - 개발 예정
8. **🧵 세션 관리**: 세션 저장/복구, LLM 기반 자동 컨텍스트 구성 - 개발 예정
9. **🧬 정교한 diff/patch**: 변경사항 분석, 패치 적용, 롤백, 자동 백업 - 개발 예정
10. **🧠 MCP (Multi-step Code Planning)**: LLM이 복잡한 요청을 단계별로 분해하여 실행 - 개발 예정
11. **🔐 권한 프롬프트**: LLM 호출, 실행 작업 등 사전 확인 시스템 - 개발 예정
12. **💾 세션 이어서 하기**: 이전 작업 컨텍스트를 저장하고 복원하는 세션 연속성 기능 - 개발 예정
13. **📄 템플릿 파일 생성**: 미리 정의된 템플릿을 바탕으로 새로운 파일을 생성하는 기능 - 개발 예정
14. **📋 공통 MD 파일 생성**: 프로젝트 전반에서 참조할 마크다운 문서를 자동 생성하는 기능 - 개발 예정
15. **📚 튜토리얼 모드**: 처음 사용자를 위한 대화형 가이드 (C/SQL/XML 파일 분석 실습) - 개발 예정
16. **⚡ 프롬프트 캐싱**: OpenAI 프롬프트 캐싱을 통한 성능 최적화 - 개발 예정
17. **👀 파일 감시**: 파일 시스템 변경 감지 및 자동 재분석 (Hot Reload) - 개발 예정
18. **🛡️ Edit GuardRail**: 파일 변경 이력 추적 및 LLM 생성 변경 이유 주석 - 개발 예정

## 실행 방법

```bash
python3 cli/main.py
```

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
- `/repo` - directory 내부 파일들 구조 분석


### 개발 예정 명령어
- `/tutorial` - 처음 사용자를 위한 대화형 튜토리얼
- `/watch <디렉토리>` - 파일 변경 감시 모드 시작/종료
- `coe test` - 테스트 실행
- `coe diff` - 변경점 확인
- `coe patch` - 수정 적용
- `coe revert` - 수정 롤백
- `coe save-session` - 세션 저장
- `coe resume` - 세션 복구
- `coe web` - Web UI 실행 (트리/그래프 시각화)
- `/continue` - 이전 세션 이어서 시작하기

## 파일 타입별 특화 분석 시스템 ✅

### C 파일 (.c) - IO Formatter 중심 분석
C 파일 전용 프롬프트로 다음 요소들을 중점 분석합니다:

**핵심 분석 대상:**
- **IO Formatter**: 입출력 구조체 분석
- **c000_main_proc**: 메인 프로세스 로직 분석  
- **DBIO 호출 패턴**: 어떤 DBIO 함수를 호출하여 출력을 생성하는지 분석

**표준 함수 구조 자동 인식:**
- `a000_init_proc`: 프로그램 초기화 함수
- `b000_input_validation`: 입력 데이터 검증 수행
- `c000_main_proc`: 실제 프로그램의 주요 로직 처리
- `z999_err_exit_proc`: 프로그램 에러 종료 처리

### XML 파일 (.xml) - TrxCode 중심 분석
XML 파일 전용 프롬프트로 다음 요소들을 중점 분석합니다:

**핵심 분석 대상:**
- **TrxCode 호출 패턴**: 어떤 TrxCode를 호출하고 있는지 분석
- **TrxCode 함수 바디**: TrxCode가 있는 함수를 중점적으로 분석
- **UI 컴포넌트**: 그리드, 입력필드, 버튼, 데이터셋 분석
- **JavaScript 함수**: scwin.xxx 형태의 함수 분석
- **데이터 흐름**: 입력 필드와 출력 결과의 매핑 관계

### SQL 파일 (.sql) - 입출력 및 테이블 조인 중심 분석
SQL 파일 전용 프롬프트로 다음 요소들을 중점 분석합니다:

**핵심 분석 대상:**
- **입출력 값 분석**: 바인드 변수(:variable)와 SELECT 결과 컬럼의 nullable 여부
- **테이블 조인 관계**: 어떤 테이블을 조인하고 있는지와 조인 목적 분석
- **Oracle 특화 기능**: 힌트, 함수, (+) 조인 등 사용 패턴 분석
- **성능 최적화**: 쿼리 복잡도와 최적화 제안사항

**Oracle SQL 특징 자동 분석:**
- **오라클 힌트**: `/*+ index(...) use_nl(...) */` 등의 성능 최적화 힌트
- **바인드 변수**: `:svc_mgmt_num`, `:bas_dt` 등의 파라미터 및 nullable 정보
- **아우터 조인**: Oracle 전용 `(+)` 구문
- **오라클 함수**: NVL, TO_CHAR, SYSDATE 등
- **특수 날짜 패턴**: `99991231235959`, `99991231` 등의 무한대 날짜 패턴

### 일반 파일 (기타) - 기본 분석
기타 파일 타입에 대해서는 일반적인 코드 분석을 수행합니다:
- 파일 목적 (주석 우선 추출)
- 주요 함수 및 의존성 분석
- 입출력 파라미터의 nullable 정보 포함

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
- 모듈화된 구조 유지 (cli, actions, llm, prompts 모듈 분리)
- 한국어 사용자 친화적 메시지 제공
- **파일 타입별 특화 분석**: 파일 확장자에 따라 적절한 전용 프롬프트 사용
- **nullable 정보 필수**: 모든 입출력 파라미터에 nullable 여부 포함
- **디버그 로그 유지**: LLM 분석 과정의 투명성을 위해 디버그 정보 출력
- **Rich 테이블 형식**: 분석 결과를 보기 좋은 표 형태로 출력

## 새로운 기능 상세 설명

### 📚 튜토리얼 모드 (개발 예정)

**목적**: 처음 사용하는 사용자가 실제 파일로 Swing CLI의 주요 기능을 체험할 수 있는 대화형 가이드

**기능**:
- `test_with_fixtures.py` 기반의 실습 시나리오
- C, SQL, XML 파일별 특화 분석 실습
- 단계별 Enter 키를 통한 진행/스킵 가능
- 실제 `tests/fixtures/` 파일들을 사용한 체험

**튜토리얼 단계**:
1. **파일 추가 체험**: `ORDSS04S2050T01.c`, `ZORDSS0340082.XML`, `zord_svc_prod_grp_s0001.sql` 파일 추가
2. **C 파일 분석**: IO Formatter 패턴, 함수 구조, DBIO 호출 분석
3. **XML 파일 분석**: TrxCode 패턴, UI 컴포넌트, JavaScript 함수 분석
4. **SQL 파일 분석**: 바인드 변수, 테이블 조인, Oracle 힌트 분석
5. **질문/편집 실습**: Ask/Edit 모드로 실제 코드 분석 및 수정

### ⚡ 프롬프트 캐싱 (개발 예정)

**목적**: OpenAI API 프롬프트 캐싱을 활용한 성능 최적화 및 비용 절감

**기능**:
- 반복적으로 사용되는 시스템 프롬프트 캐싱
- 파일별 특화 분석 프롬프트 캐싱 (C/SQL/XML)
- 컨텍스트 프롬프트 자동 캐싱
- 캐시 히트율 모니터링 및 통계

**구현 방식**:
```python
# 예시 구현
class PromptCacheManager:
    def cache_system_prompt(self, file_type: str, prompt: str):
        """파일 타입별 시스템 프롬프트 캐싱"""

    def get_cached_prompt(self, cache_key: str):
        """캐싱된 프롬프트 반환"""

    def invalidate_cache(self, pattern: str):
        """캐시 무효화"""
```

### 👀 파일 감시 기능 (개발 예정)

**목적**: 파일 시스템 변경을 실시간으로 감지하고 자동으로 재분석 수행

**기능**:
- `watchdog` 라이브러리 기반 파일 시스템 감시
- 지정된 디렉토리의 .c, .sql, .xml 파일 변경 감지
- 변경 감지 시 자동 재분석 및 컨텍스트 업데이트
- Hot Reload 방식의 실시간 분석 결과 반영

**명령어**:
```bash
> /watch ./src                    # ./src 디렉토리 감시 시작
> /watch stop                     # 감시 중지
> /watch status                   # 감시 상태 확인
```

**구현 방식**:
```python
# 예시 구현
class FileWatcher:
    def start_watching(self, directory: str, extensions: List[str]):
        """파일 감시 시작"""

    def on_file_modified(self, event):
        """파일 변경 이벤트 핸들러"""
        # 자동 재분석 수행
        # 컨텍스트 업데이트
        # 사용자에게 알림
```

### 🛡️ Edit GuardRail (개발 예정)

**목적**: 파일 변경 이력을 체계적으로 추적하고 변경 이유를 자동으로 문서화

**기능**:
- 모든 파일 편집에 대한 메타데이터 기록
- LLM이 변경 이유를 자동으로 생성하여 주석으로 삽입
- 누가(사용자), 언제(타임스탬프), 어디를(파일:라인), 왜(LLM 생성 이유) 변경했는지 추적
- Git 스타일의 blame 기능과 연동

**주석 형태**:
```c
// [SWING-CLI] 2024-01-15 14:30:25 by user123
// [변경이유] 입력 검증 로직 강화를 위해 NULL 체크 추가
if (input_data == NULL) {
    return ERROR_INVALID_INPUT;
}
```

**구현 방식**:
```python
class EditGuardRail:
    def log_change(self, file_path: str, line_range: tuple,
                   change_reason: str, user: str):
        """변경 이력 기록"""

    def generate_change_comment(self, old_code: str, new_code: str) -> str:
        """LLM을 통한 변경 이유 생성"""

    def insert_change_metadata(self, file_path: str, line_num: int,
                              metadata: str):
        """파일에 변경 메타데이터 주석 삽입"""
```

# 🚧 다음 세션 우선 작업 항목

## 📋 **CoeAnalyzer 캐싱 시스템 구현**

### **🎯 구현 계획 단계:**

#### **1단계: CoeAnalyzer 캐싱 시스템 설계 ✅**
- **목표**: Ask 모드에서 사용자가 구조 분석 요청 시 실행하고 결과 캐싱
- **캐싱 범위**: RepoMap과 유사한 방식으로 파일별 분석 결과 저장
- **트리거**: "구조 분석", "분석해줘", "어떤 파일이야" 등의 키워드 감지

#### **2단계: Context Manager에 CoeAnalyzer 캐싱 추가**
- **파일**: `cli/core/context_manager.py`
- **기능 추가**:
  ```python
  class PromptBuilder:
      def __init__(self, task: str):
          self._coe_analysis_cache = {}  # 파일별 CoeAnalyzer 결과 캐싱

      def get_cached_coe_analysis(self, file_path: str) -> Optional[Dict]:
          """캐싱된 CoeAnalyzer 분석 결과 반환"""

      def perform_coe_analysis_on_demand(self, file_path: str, file_manager) -> Dict:
          """요청 시에만 CoeAnalyzer 실행하고 캐싱"""
  ```

#### **3단계: Ask 모드 키워드 감지 시스템**
- **파일**: `cli/ui/interactive.py` 또는 새 모듈
- **기능**:
  ```python
  def detect_structure_analysis_request(user_input: str, file_manager) -> Dict:
      """구조 분석 요청 감지 및 대상 파일 추출"""
      keywords = ['구조 분석', '분석해줘', '어떤 파일', '파일 구조', '코드 분석']
      # 파일 경로 패턴과 키워드 매칭
  ```

#### **4단계: Main CLI에서 분석 요청 처리**
- **파일**: `cli/main.py`
- **위치**: Ask 모드 처리 로직 내
- **처리 흐름**:
  1. 사용자 입력에서 구조 분석 키워드 감지
  2. 대상 파일 추출 (예: "ORDSS04S2050T01.c 구조 분석해줘")
  3. 해당 파일이 컨텍스트에 있는지 확인
  4. CoeAnalyzer 실행 (캐시 확인 후 필요시에만)
  5. 분석 결과를 프롬프트에 포함하여 LLM 호출

#### **5단계: 프롬프트에 CoeAnalyzer 결과 통합**
- **파일**: `cli/core/context_manager.py`의 `build()` 메서드
- **기능**:
  ```python
  def build(self, user_input: str, file_context: Dict, history: List, file_manager=None) -> List:
      # 기존 로직...

      # CoeAnalyzer 결과가 있으면 프롬프트에 추가
      coe_analysis = self._get_relevant_coe_analysis(user_input, file_context)
      if coe_analysis:
          for file_path, analysis in coe_analysis.items():
              analysis_str = f"File Structure Analysis for {file_path}:\n{json.dumps(analysis, ensure_ascii=False, indent=2)}"
              messages.append({"role": "system", "content": analysis_str})
  ```

#### **6단계: 디버그 출력 및 캐시 상태 확인**
- **기능**: 어떤 파일에 대해 CoeAnalyzer 결과가 캐싱되어 있는지 확인
- **명령어**: `/coe-cache` 또는 기존 `/files` 명령어에 통합
- **디버그**: DebugManager에 CoeAnalyzer 관련 로깅 추가

### **🎨 CoeAnalyzer 캐싱 구조:**
```python
# context_manager.py
class PromptBuilder:
    def __init__(self, task: str):
        self._coe_analysis_cache = {
            "file_path": {
                "timestamp": "2024-xx-xx",
                "analysis": {
                    "purpose": "...",
                    "key_functions": {...},
                    "io_formatter_analysis": {...},
                    "c000_main_proc_analysis": {...},
                    "dbio_analysis": {...}
                }
            }
        }
```

### **📍 수정 대상 파일:**
- `cli/core/context_manager.py` (주요 캐싱 로직)
- `cli/main.py` (Ask 모드에서 분석 요청 처리)
- `cli/ui/interactive.py` (키워드 감지 함수)
- `cli/core/debug_manager.py` (CoeAnalyzer 디버그 출력)

### **✅ 완료 조건:**
- `/add` 시에는 CoeAnalyzer 실행하지 않음 (성능 개선)
- Ask 모드에서 구조 분석 키워드 감지 시 자동으로 CoeAnalyzer 실행
- 분석 결과가 프롬프트에 포함되어 더 정확한 답변 제공
- 캐싱으로 동일 파일 재분석 방지
- RepoMap과 유사한 방식의 일관된 캐싱 시스템

## 📋 **이전 완료된 작업들**

### **🎯 완료된 작업:**

1. **🎨 Debug 출력 전용 매니저 클래스 생성** ✅
   - `cli/core/debug_manager.py` 새 파일 생성 완료
   - `DebugManager` 클래스 with Rich Console 통합 완료
   - 색깔 코드 통일 (RepoMap=cyan, FileAnalysis=yellow, Error=red) 완료

2. **🔄 기존 디버그 출력 교체** ✅
   - 모든 `print("[RepoMap DEBUG]")` → `DebugManager.repo_map()` 교체 완료
   - `cli/coders/repo_mapper.py` 수정 완료
   - `cli/core/context_manager.py` 수정 완료

3. **🚫 file_manager add 후 자동 AI 분석 제거** ✅
   - `actions/file_manager.py`의 `add()` 메서드에서 LLM 호출 부분 제거 완료
   - 기본 파일 분석만 유지 (파일 타입, 크기 등) 완료

4. **⚡ RepoMap 수동 생성 모드** ✅
   - `/repo` 명령어로 수동 RepoMap 생성 시스템 구현 완료
   - RepoMap 캐싱 시스템 구현 완료

5. **🔧 파일 경로 해결 시스템** ✅
   - `cli/coders/repo_mapper.py` 수정
   - `_scan_repository()` 메서드를 `tests/fixtures/` 경로만 스캔하도록 제한
   - `_collect_priority_files()` 메서드도 동일하게 제한

### **🎨 DebugManager 구조:**
```python
class DebugManager:
    @staticmethod
    def repo_map(message)      # [cyan] RepoMap 관련
    def file_analysis(message) # [yellow] 파일 분석 관련
    def context(message)       # [blue] 컨텍스트 관련
    def error(message)         # [red] 에러 관련
```

### **📍 수정 대상 파일:**
- `cli/core/debug_manager.py` (신규)
- `cli/coders/repo_mapper.py`
- `cli/core/context_manager.py`
- `actions/file_manager.py`

### **✅ 완료 조건:**
- 모든 디버그 출력이 통일된 색깔로 표시
- `/add` 명령어가 빠르게 동작 (자동 AI 분석 없음)
- 질문 시 즉시 레포맵 생성
- 레포맵이 tests/fixtures 파일만 대상으로 함
