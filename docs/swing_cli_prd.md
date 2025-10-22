# Swing CLI – Product Requirements Document (PRD)

## 1. 제품 개요
`Swing CLI`는 대화형 CLI 도구로, 개발자가 코드에 대해 **질문**, **수정**, **테스트**, **구조 분석**을 할 수 있도록 지원합니다.  
LLM(대규모 언어 모델) 백엔드를 통해 파일을 분석하고, 다양한 언어(C, SQL, XML 등)에 특화된 분석 결과를 제공합니다.

---

## 2. 목표 및 가치
- **개발자 생산성 향상**: 코드 리뷰, 구조 이해, 테스트 실행을 CLI 상에서 바로 가능하게 함
- **운영 안정성 강화**: 배포 전 코드 검토 및 시스템 분석 지원
- **학습 곡선 완화**: 신규 팀원이 빠르게 프로젝트 구조와 로직을 이해할 수 있도록 돕는 도구 제공

---

## 3. 타겟 사용자
- **개발자**: Python, C, SQL, XML 등 다양한 언어 기반 프로젝트를 다루는 팀
- **운영자/시스템 관리자**: 유지보수, 배포 전 코드 검토, 운영 안정성 확보가 필요한 역할

---

## 4. 성공 지표
- CLI 기반 코드 분석 요청에 대한 **평균 응답 시간** (≤ 2초 캐시된 경우, ≤ 10초 비캐시 경우)
- **코드 구조 분석 정확도** (사용자 평가 기준 ≥ 80% 이해도 만족도)
- **세션 복구 성공률** (저장/복구 기능 도입 후 ≥ 95%)
- **테스트 실행 성공률** (CLI 내 자동 테스트 시 오류 없는 실행 비율 ≥ 90%)

---

## 5. 주요 기능 요구사항

### 5.1 핵심 기능
1. **LLM 기반 코드 구조 분석**  
   - 계층 구조, 호출 관계, 주요 로직 요약
   - 파일 타입별 특화 분석 (C, XML, SQL)
   - JSON 응답을 자동 변환해 테이블로 표시

2. **대화형 CLI (REPL)**  
   - `prompt_toolkit` 기반 인터페이스
   - 자동완성, 명령어 지원 (`/add`, `/ask`, `/edit`, `/test` 등)

3. **온디맨드 분석**  
   - 파일 추가 시 기본 분석만 수행  
   - "구조 분석" 요청 시 `CodeAnalyzer` 실행

4. **디버그/투명성 기능**  
   - LLM 호출 과정 로깅
   - `/debug` 명령으로 상세 추적 가능

---

### 5.2 차별화 기능
- **파일 타입별 특화 분석**
  - **C 파일**: IO Formatter, `c000_main_proc`, DBIO 호출 패턴
  - **XML 파일**: TrxCode 호출, UI 컴포넌트, JS 함수
  - **SQL 파일**: 입출력 값, 조인 관계, 오라클 특화 기능
- **특수 용어 인식**: DBIO 관련 질문 자동 인식 및 데이터베이스 분석 모드 전환

---

### 5.3 향후 확장 기능 (로드맵)
- 자동 테스트 실행 (Makefile, CMake)
- 세션 저장/복구 및 컨텍스트 관리
- diff/patch 기반 수정 및 롤백
- MCP(Multi-step Code Planning) 기반 단계적 코드 수정
- Web UI 기반 코드 구조 시각화

---

## 6. 기술 요구사항
- **Language**: Python 3.8+
- **CLI Framework**: Click
- **Interactive Interface**: prompt_toolkit
- **LLM Integration**: OpenAI API
- **HTTP Client**: requests

---

## 7. 제약사항
- 초기 버전에서는 Python, C, SQL, XML 분석에 집중
- 대규모 리포지토리에서의 성능은 캐싱 시스템 도입 후 개선 예정
- 테스트 자동화는 기본 Makefile/CMake만 지원 (향후 확장 고려)

---

### 현재 구현된 명령어
- `/add <파일>` - 파일을 컨텍스트에 추가
- `/ask` - 질문 모드
- `/edit` - 수정 모드 (whole/block/udiff 지원)
- `/test` - 테스트 실행
- `/preview` - 변경사항 미리보기
- `/apply` - 변경사항 적용
- `/help` - 도움말 표시
- `/exit` - CLI 종료
- `/repo` - 리포지토리 맵 생성


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
