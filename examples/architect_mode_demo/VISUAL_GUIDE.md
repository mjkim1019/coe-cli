# 🎨 Visual Guide - Architect Mode in Action

## The Complete Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│  YOU: Type natural language request                             │
│                                                                  │
│  > /architect "Create SQL query for customer analytics"         │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 1: AI Plan Generation                                     │
│  ────────────────────────────                                   │
│  📋 AI analyzes your request                                    │
│  🤖 LLM creates execution plan                                  │
│  ✅ Validates JSON structure                                    │
│                                                                  │
│  Output: Structured plan with steps                             │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 2: Plan Display (Rich Table)                              │
│  ────────────────────────────────────                           │
│  ┏━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━┓      │
│  ┃ Step ┃ Command ┃ Description┃ Parameters┃ Reason      ┃    │
│  ┡━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━┩    │
│  │  1   │ /add    │ Add schema │ file: ... │ Need info   │    │
│  │  2   │ /edit   │ Create SQL │ file: ... │ Implement   │    │
│  │  3   │ /test   │ Validate   │ type: ... │ Verify      │    │
│  └──────┴─────────┴────────────┴───────────┴─────────────┘    │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 3: User Approval                                          │
│  ──────────────────────                                         │
│  ❓ 이 계획을 승인하시겠습니까?                                      │
│  계획 실행을 승인하시겠습니까? [Y/n]: _                               │
│                                                                 │
│  YOU: Press Y or Enter                                          │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 4: Sequential Execution                                   │
│  ─────────────────────────────                                  │
│                                                                  │
│  🚀 계획 실행 시작                                              │
│                                                                  │
│  ▶ Step 1: Add schema file                                      │
│    [Executing /add command...]                                  │
│  ✅ Step 1 완료                                                 │
│                                                                  │
│  ▶ Step 2: Create SQL query                                     │
│    [Executing /edit command...]                                 │
│  ✅ Step 2 완료                                                 │
│                                                                  │
│  ▶ Step 3: Validate syntax                                      │
│    [Executing /test command...]                                 │
│  ✅ Step 3 완료                                                 │
│                                                                  │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 5: Save & Summary                                         │
│  ───────────────────────                                        │
│  💾 Saving to: .swmate/plans/plan_20251209_143000.yaml         │
│                                                                  │
│  📊 실행 요약:                                                  │
│     총 단계: 3                                                   │
│     성공: 3                                                      │
│     실패: 0                                                      │
│     건너뛰기: 0                                                  │
│                                                                  │
│  ✅ 모든 단계가 성공적으로 완료되었습니다!                       │
└─────────────────────────────────────────────────────────────────┘
```

## Error Handling Flow

```
┌─────────────────────────────────┐
│  Step Execution                 │
│  ▶ Step 2: Create query         │
└────────────┬────────────────────┘
             │
             ▼
      ┌──────────────┐
      │  Success?    │
      └──────┬───────┘
             │
         ┌───┴───┐
         │       │
      YES│       │NO
         │       │
         ▼       ▼
    ┌────────┐  ┌──────────────────────────┐
    │ ✅ OK  │  │  ❌ Step 2 실패           │
    └────────┘  │  File not found          │
                │                          │
                │  다음 조치를 선택하세요:  │
                │  1. stop - 전체 중단     │
                │  2. skip - 건너뛰기      │
                └──────┬───────────────────┘
                       │
                   ┌───┴───┐
                   │       │
                STOP│     │SKIP
                   │       │
                   ▼       ▼
            ┌──────────┐  ┌──────────┐
            │ 실행 중단 │  │ 다음단계  │
            └──────────┘  └──────────┘
```

## Real Example - Screenshot Simulation

### Before Execution
```
> /architect "Create query for long-term customers"

🏗️  Architect Mode 시작

요청: Create query for long-term customers

📋 실행 계획 생성 중...
✅ 실행 계획이 생성되었습니다.

┏━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┓
┃ Step ┃ Command ┃ Description                  ┃ Parameters     ┃ Reason              ┃
┡━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━┩
│  1   │ /add    │ Add customer schema          │ file: schema   │ Need table info     │
│  2   │ /edit   │ Create long-term query       │ file: query    │ Business logic      │
│  3   │ /test   │ Validate SQL syntax          │ type: syntax   │ Ensure correctness  │
└──────┴─────────┴──────────────────────────────┴────────────────┴─────────────────────┘

❓ 이 계획을 승인하시겠습니까?
계획 실행을 승인하시겠습니까? [Y/n]: _
```

### During Execution
```
계획 실행을 승인하시겠습니까? [Y/n]: y
✅ 계획이 승인되었습니다.

🚀 계획 실행 시작

▶ Step 1: Add customer schema
  Added 1 file(s)
✅ Step 1 완료

▶ Step 2: Create long-term query
  파일 수정: long_term_customers.sql
  작업: Create query for customers with 3+ years
✅ Step 2 완료

▶ Step 3: Validate SQL syntax
  테스트 타입: syntax
  대상 파일: long_term_customers.sql
✅ Step 3 완료

✅ 모든 단계가 성공적으로 완료되었습니다!

성공: 3, 실패: 0, 건너뛰기: 0

💾 계획이 저장되었습니다: .swmate/plans/plan_20251209_143000.yaml

✅ Architect Mode 완료!
계획 ID: 20251209_143000
상태: completed

📊 실행 요약:
  총 단계: 3
  성공: 3
  실패: 0
  건너뛰기: 0
```

## File Structure After Execution

```
your-project/
├── .swmate/
│   └── plans/
│       ├── plan_20251209_143000.yaml  ← Your execution history
│       ├── plan_20251209_144530.yaml
│       └── plan_20251209_150215.yaml
│
├── examples/
│   └── architect_mode_demo/
│       └── customer_schema.sql  ← Files you worked with
│
└── long_term_customers.sql  ← Generated query (if edit was run)
```

## Plan File Structure (YAML)

```yaml
plan_id: "20251209_143000"
description: "Create query for long-term customers"
created_at: "2025-12-09T14:30:00.123456"
status: "completed"

steps:
  - step_number: 1
    command: "/add"
    description: "Add customer schema"
    parameters:
      file: "customer_schema.sql"
    reason: "Need table info"
    status: "success"        ← Track each step
    output: "Added 1 file(s)"
    error: null
    
  - step_number: 2
    command: "/edit"
    description: "Create long-term query"
    parameters:
      file: "long_term_customers.sql"
      action: "Create query for 3+ year customers"
    reason: "Business logic"
    status: "success"
    output: "Edit operation queued"
    error: null
    
  - step_number: 3
    command: "/test"
    description: "Validate SQL syntax"
    parameters:
      type: "syntax"
      file: "long_term_customers.sql"
    reason: "Ensure correctness"
    status: "success"
    output: "Test passed"
    error: null

results: []
```

## Key Visual Elements

### 📋 Plan Table
- **Clear structure** - See all steps at a glance
- **Color-coded** - Commands, params, reasons
- **Rich formatting** - Professional appearance

### ✅ Progress Indicators
- **▶** - Currently executing
- **✅** - Successfully completed
- **❌** - Failed (with error details)
- **⏭** - Skipped

### 🎨 Status Colors
- **Green** - Success messages
- **Yellow** - Warnings, approvals
- **Red** - Errors
- **Cyan** - Information, progress
- **Dim** - Detailed output

## Interactive Elements

```
┌────────────────────────────────────┐
│  User Input Points:                │
├────────────────────────────────────┤
│  1. Initial request                │
│     /architect "..."               │
│                                    │
│  2. Plan approval                  │
│     [Y/n]: _                       │
│                                    │
│  3. Error handling (if needed)     │
│     [stop/skip]: _                 │
│                                    │
│  4. Exec confirmation (if needed)  │
│     [y/N]: _                       │
└────────────────────────────────────┘
```

---

**Visual learner?** This shows exactly what you'll see when using Architect Mode! 🎨
