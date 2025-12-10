# Architect Mode - AI Task Orchestration

Architect Mode는 복잡한 자연어 요청을 자동으로 실행 가능한 계획으로 변환하고, 단계별로 실행하는 AI 작업 자동화 엔진입니다.

## 개요

사용자가 자연어로 작업을 요청하면, LLM이 이를 분석하여 단계별 실행 계획(Plan)을 생성합니다. 
사용자가 계획을 승인하면, 시스템이 각 단계를 순차적으로 실행하고 결과를 저장합니다.

## 주요 기능

### 1. Plan Generation (계획 생성)
- 자연어 요청을 LLM에 전달
- JSON 형식의 실행 계획 자동 생성
- 각 단계별 명령어, 설명, 매개변수, 이유 포함

### 2. Plan Visualization & Approval (계획 시각화 및 승인)
- Rich 테이블 형식으로 계획 표시
- 사용자가 전체 계획 승인/거부 선택
- 향후: 개별 단계별 승인 기능 추가 예정

### 3. Sequential Execution (순차 실행)
- 승인된 계획을 단계별로 순차 실행
- 각 단계의 성공/실패 기록
- 실패 시 사용자 선택:
  - **중단(stop)**: 전체 실행 중단
  - **건너뛰기(skip)**: 해당 단계 건너뛰고 계속
  - **재시도(retry)**: [향후 구현] 단계 재실행
  - **수정(modify)**: [향후 구현] 단계 수정 후 재실행

### 4. State Saving (상태 저장)
- 모든 계획과 실행 결과를 `.swmate/plans/` 디렉토리에 YAML 형식으로 저장
- 계획 ID로 이전 계획 복원 가능
- 추적 가능성(traceability) 제공

## 사용 방법

### 기본 사용법

```bash
# Architect Mode 시작
/architect "유선 회선 기준으로 유무선 결합 가입년수 합산값 조회하는 쿼리 개발해줘"

# 1. LLM이 실행 계획 생성
# 2. 계획이 테이블로 표시됨
# 3. 승인 여부 선택
# 4. 승인 시 각 단계가 순차 실행
# 5. 결과가 .swmate/plans/plan_YYYYMMDD_HHMMSS.yaml에 저장
```

### 지원 명령어

Architect Mode는 다음 명령어들을 계획에 포함할 수 있습니다:

- `/edit`: 파일 수정
- `/exec`: 명령어 실행 (컴파일, 빌드 등)
- `/test`: 테스트 실행
- `/add`: 파일 추가

## 실행 계획 예시

```json
{
  "steps": [
    {
      "step_number": 1,
      "command": "/add",
      "description": "분석할 테이블 스키마 파일 추가",
      "parameters": {
        "file": "schema/customer_table.sql"
      },
      "reason": "쿼리 작성을 위해 테이블 구조 파악 필요"
    },
    {
      "step_number": 2,
      "command": "/edit",
      "description": "유무선 결합 가입년수 조회 쿼리 생성",
      "parameters": {
        "file": "queries/customer_subscription.sql",
        "action": "유선 회선 기준 유무선 결합 가입년수 합산 쿼리 작성"
      },
      "reason": "요청된 비즈니스 로직 구현"
    },
    {
      "step_number": 3,
      "command": "/test",
      "description": "쿼리 구문 검증",
      "parameters": {
        "type": "syntax",
        "file": "queries/customer_subscription.sql"
      },
      "reason": "SQL 문법 오류 확인"
    }
  ]
}
```

## 저장된 계획 구조

계획은 YAML 형식으로 저장됩니다:

```yaml
plan_id: "20251208_140305"
description: "유선 회선 기준으로 유무선 결합 가입년수 합산값 조회하는 쿼리 개발해줘"
created_at: "2025-12-08T14:03:05.123456"
status: "completed"  # pending, approved, executing, completed, failed
steps:
  - step_number: 1
    command: "/add"
    description: "분석할 테이블 스키마 파일 추가"
    parameters:
      file: "schema/customer_table.sql"
    reason: "쿼리 작성을 위해 테이블 구조 파악 필요"
results:
  - step_number: 1
    status: "success"
    output: "파일 'schema/customer_table.sql' 추가 완료"
  - step_number: 2
    status: "success"
    output: "파일 'queries/customer_subscription.sql' 편집 완료"
```

## 아키텍처

### 클래스 구조

```
ArchitectMode (메인 엔진)
├── generate_plan()          # Step 1: Plan 생성
├── visualize_plan()         # Step 2: Plan 시각화
├── approve_plan()           # Step 2: 승인 요청
├── execute_plan()           # Step 3: 순차 실행
│   ├── _execute_step()
│   ├── _execute_edit()
│   ├── _execute_exec()
│   ├── _execute_test()
│   └── _execute_add()
├── save_plan()              # Step 4: 상태 저장
├── load_plan()              # 계획 복원
└── list_plans()             # 계획 목록

ExecutionPlan (데이터 구조)
├── to_dict()                # 직렬화
└── from_dict()              # 역직렬화
```

### 실행 흐름

```
사용자 요청
    ↓
[Step 1] LLM에게 Plan 생성 요청
    ↓
[Step 2] Plan 시각화 (Rich Table)
    ↓
[Step 2] 사용자 승인 요청
    ↓ (승인 시)
[Step 3] 단계별 순차 실행
    ├─→ 성공 → 다음 단계
    └─→ 실패 → 사용자 선택 (중단/건너뛰기/재시도/수정)
    ↓
[Step 4] 결과를 YAML 파일로 저장
```

## 향후 개발 계획

### P1 (우선순위 높음)
- [ ] 실제 `/edit`, `/exec`, `/test` 명령 실행 로직 연동
- [ ] 단계 실패 시 재시도(retry) 기능
- [ ] 단계별 개별 승인 기능
- [ ] 계획 템플릿 기능 (자주 사용하는 패턴 저장)

### P2 (중간 우선순위)
- [ ] 계획 이력 조회 및 복원 (`/resume` 명령)
- [ ] 계획 수정 기능 (단계 추가/삭제/변경)
- [ ] 병렬 실행 지원 (독립적인 단계들 동시 실행)
- [ ] 진행 상황 실시간 표시 (Progress Bar)

### P3 (장기 계획)
- [ ] 계획 시뮬레이션 (Dry-run 모드)
- [ ] 계획 공유 및 재사용 (Export/Import)
- [ ] 계획 성능 분석 및 최적화 제안
- [ ] Web UI 연동

## 예제 시나리오

### 시나리오 1: Text-to-SQL

```bash
/architect "고객별 월별 매출 합계를 조회하는 SQL 쿼리 개발해줘"

# 예상 Plan:
# 1. /add - 고객 테이블 스키마 추가
# 2. /add - 매출 테이블 스키마 추가
# 3. /edit - SQL 쿼리 파일 생성
# 4. /test - 쿼리 구문 검증
```

### 시나리오 2: 버그 수정

```bash
/architect "login.c 파일의 메모리 누수 버그 찾아서 수정해줘"

# 예상 Plan:
# 1. /add - login.c 파일 추가
# 2. /ask - 메모리 누수 패턴 분석
# 3. /edit - 메모리 누수 수정
# 4. /exec - 컴파일 테스트
# 5. /test - 메모리 검사 실행
```

### 시나리오 3: 새 기능 개발

```bash
/architect "사용자 인증 API 엔드포인트 개발해줘"

# 예상 Plan:
# 1. /new - API 파일 템플릿으로 생성
# 2. /edit - 인증 로직 구현
# 3. /edit - 테스트 코드 작성
# 4. /test - 단위 테스트 실행
# 5. /exec - 통합 테스트 실행
```

## 문제 해결

### Q: 계획 생성 시 JSON 파싱 오류가 발생합니다
A: LLM이 유효하지 않은 JSON을 생성한 경우입니다. 기본 계획이 생성되며, 더 구체적인 요청으로 재시도하세요.

### Q: 단계 실행이 실패했습니다
A: 실패 시 선택 메뉴가 표시됩니다. "중단", "건너뛰기", "재시도", "수정" 중 선택할 수 있습니다.

### Q: 이전 계획을 다시 실행하고 싶습니다
A: 향후 `/resume <plan_id>` 명령으로 이전 계획을 불러올 수 있습니다. (개발 예정)

### Q: 계획을 수정하고 싶습니다
A: 현재는 계획 승인 전에만 거부 가능합니다. 계획 수정 기능은 향후 추가 예정입니다.

## 기여 가이드

Architect Mode 개선에 기여하려면:

1. 새로운 명령어 추가: `_execute_<command_name>()` 메서드 구현
2. Plan 생성 프롬프트 개선: `_create_plan_generation_prompt()` 수정
3. 실행 결과 시각화 개선: `visualize_plan()` 메서드 확장
4. 오류 처리 강화: `_handle_step_failure()` 로직 개선

## 관련 문서

- [기능 로드맵](features_sepc_roadmap.md)
- [메인 명세서](swing_cli_prd.md)
- [개발 컨벤션](development_convention.md)
