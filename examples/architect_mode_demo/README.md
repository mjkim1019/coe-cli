# Architect Mode - Complete Example Walkthrough

This example demonstrates how to use Architect Mode to automatically create a SQL query analysis project.

## Scenario

You want to create a query that analyzes customer subscription data, specifically:
- Find customers with subscriptions longer than 3 years
- Calculate subscription duration
- Filter by active status

Instead of manually creating files and writing SQL, you'll use `/architect` to do it all automatically.

## Step-by-Step Walkthrough

### 1. Prepare Your Environment

First, make sure you have the sample schema file:

```bash
cd examples/architect_mode_demo
ls
# You should see: customer_schema.sql
```

### 2. Start Swing CLI

```bash
cd /home/tungdv15/coe-cli
python run.py
```

### 3. Use Architect Mode

Type the following command in the CLI:

```bash
/architect "Create a SQL query to find customers with subscriptions longer than 3 years, include subscription duration calculation"
```

### 4. What Happens Next

#### Step 1: Plan Generation

The AI will analyze your request and generate an execution plan. You'll see something like:

```
📋 실행 계획 생성 중...
✅ 실행 계획이 생성되었습니다.
```

#### Step 2: Plan Display

A beautiful table will appear:

```
┏━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Step ┃ Command ┃ Description                      ┃ Parameters        ┃ Reason                ┃
┡━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━┩
│  1   │ /add    │ Add customer schema file         │ file: customer... │ Need table structure  │
│  2   │ /edit   │ Create subscription query        │ file: long_sub... │ Implement logic       │
│  3   │ /test   │ Validate SQL syntax              │ type: syntax      │ Ensure correctness    │
└──────┴─────────┴──────────────────────────────────┴───────────────────┴───────────────────────┘
```

#### Step 3: Approval

You'll be asked:

```
❓ 이 계획을 승인하시겠습니까?
계획 실행을 승인하시겠습니까? [Y/n]:
```

**Press `Y` or just `Enter` to approve**

#### Step 4: Execution

Watch as each step executes:

```
🚀 계획 실행 시작

▶ Step 1: Add customer schema file
  [Adding examples/architect_mode_demo/customer_schema.sql]
✅ Step 1 완료

▶ Step 2: Create subscription query
  파일 수정: long_subscription_customers.sql
  작업: Create query to find customers with 3+ year subscriptions
✅ Step 2 완료

▶ Step 3: Validate SQL syntax
  테스트 타입: syntax
  대상 파일: long_subscription_customers.sql
✅ Step 3 완료
```

#### Step 5: Completion

You'll see a summary:

```
✅ 모든 단계가 성공적으로 완료되었습니다!

성공: 3, 실패: 0, 건너뛰기: 0

💾 계획이 저장되었습니다: .swmate/plans/plan_20251209_143000.yaml

📊 실행 요약:
  총 단계: 3
  성공: 3
  실패: 0
  건너뛰기: 0
```

### 5. Check the Results

The plan has been saved to:
```bash
.swmate/plans/plan_20251209_143000.yaml
```

View the saved plan:
```bash
cat .swmate/plans/plan_20251209_143000.yaml
```

## Example Output

### Saved Plan (YAML)

```yaml
plan_id: "20251209_143000"
description: "Create a SQL query to find customers with subscriptions longer than 3 years"
created_at: "2025-12-09T14:30:00.123456"
status: "completed"
steps:
  - step_number: 1
    command: "/add"
    description: "Add customer schema file"
    parameters:
      file: "examples/architect_mode_demo/customer_schema.sql"
    reason: "Need table structure to write accurate query"
    status: "success"
    output: "Added 1 file(s)"
    error: null
    
  - step_number: 2
    command: "/edit"
    description: "Create subscription query"
    parameters:
      file: "long_subscription_customers.sql"
      action: "Create query with subscription duration calculation"
    reason: "Implement the business logic"
    status: "success"
    output: "Edit operation queued: Create subscription query"
    error: null
    
  - step_number: 3
    command: "/test"
    description: "Validate SQL syntax"
    parameters:
      type: "syntax"
      file: "long_subscription_customers.sql"
    reason: "Ensure query is syntactically correct"
    status: "success"
    output: "Test 'syntax' on 'long_subscription_customers.sql' passed"
    error: null
    
results: []
```

## More Examples to Try

### Example 1: Text-to-SQL (Korean)
```bash
/architect "유선 회선 기준으로 유무선 결합 가입년수 합산값 조회하는 쿼리 개발해줘"
```

### Example 2: Data Analysis
```bash
/architect "Analyze the customer schema and create a report showing subscription type distribution"
```

### Example 3: Bug Fix Simulation
```bash
/architect "Review the customer schema and suggest optimizations for better query performance"
```

### Example 4: Multiple Files
```bash
/architect "Create a comprehensive customer analytics package with multiple queries for active customers, churned customers, and subscription upgrades"
```

## Understanding the Workflow

```
You Type Request
       ↓
AI Generates Plan (JSON)
       ↓
Plan Displayed (Rich Table)
       ↓
You Approve (Y/n)
       ↓
Steps Execute One-by-One
       ↓
Results Saved (YAML)
       ↓
Summary Displayed
```

## Handling Failures

If a step fails, you'll see:

```
❌ Step 2 실패: File not found

다음 조치를 선택하세요:
  1. 중단 (stop) - 전체 실행 중단
  2. 건너뛰기 (skip) - 이 단계를 건너뛰고 계속

선택 [stop/skip]:
```

**Options:**
- Type `stop` to halt everything
- Type `skip` to continue with remaining steps

## Tips for Success

1. **Be Specific**: Instead of "create query", say "create query to find active premium customers"

2. **Mention Files**: If you have specific files, mention them: "using customer_schema.sql"

3. **State Goals**: Include what you want: "that returns customer names and subscription dates"

4. **Use Natural Language**: Write as you would explain to a colleague

## What Gets Created

After running this example, you'll have:

1. **Query File**: `long_subscription_customers.sql` (if edit was implemented)
2. **Plan File**: `.swmate/plans/plan_YYYYMMDD_HHMMSS.yaml`
3. **Session History**: All files added to the current CLI session

## Next Steps

- Try more complex requests
- Experiment with different commands
- Review saved plans in `.swmate/plans/`
- Read [ARCHITECT_MODE_IMPLEMENTATION.md](../../docs/ARCHITECT_MODE_IMPLEMENTATION.md) for details

## Troubleshooting

**Problem**: "No file parameter provided"
**Solution**: The AI needs to specify file paths. Try rephrasing your request to be more specific.

**Problem**: "JSON parsing error"
**Solution**: The LLM response wasn't valid JSON. Try again with a clearer request.

**Problem**: Nothing happens after approval
**Solution**: Check your COE_BACKEND_URL environment variable is set correctly.

## Clean Up

To clean up after testing:
```bash
rm -rf .swmate/plans/
```

---

**Ready to try it yourself?** Just run `python run.py` and type `/architect` followed by your request! 🚀
