# Architect Mode - Quick Start Guide

## What is Architect Mode?

Architect Mode is an AI-powered task orchestration feature that automatically breaks down your natural language requests into executable plans.

Instead of manually running multiple commands, you describe what you want, and the AI creates and executes a complete plan.

## Quick Start

### 1. Start Swing CLI
```bash
python run.py
```

### 2. Use the /architect command
```bash
/architect "your natural language request here"
```

## Examples

### Example 1: Create a SQL Query
```bash
/architect "Create a query to find customers with subscription over 5 years"
```

**What happens:**
1. AI generates a plan with steps like:
   - Add relevant schema files
   - Create SQL query file
   - Test query syntax
2. Shows you the plan in a table
3. Asks for approval
4. Executes each step
5. Saves the plan

### Example 2: Fix a Bug
```bash
/architect "Fix memory leak in the authentication module"
```

**What happens:**
1. Add auth module files
2. Analyze for memory leaks
3. Apply fixes
4. Compile and test
5. Verify no leaks remain

### Example 3: Add New Feature
```bash
/architect "Add user profile API endpoint with validation"
```

**What happens:**
1. Add existing API files for context
2. Create endpoint file
3. Add input validation
4. Create tests
5. Run tests

## Command Syntax

```bash
/architect "<natural language request>"
```

**Tips:**
- Be specific about what you want
- Mention relevant files if known
- Include expected outcomes
- Use your natural language (English, Korean, etc.)

## Understanding the Plan Display

When you run `/architect`, you'll see a table like this:

```
┌──────┬─────────┬────────────────────┬────────────────┬─────────────────┐
│ Step │ Command │ Description        │ Parameters     │ Reason          │
├──────┼─────────┼────────────────────┼────────────────┼─────────────────┤
│  1   │ /add    │ Add schema file    │ file: db.sql   │ Need structure  │
│  2   │ /edit   │ Create query       │ file: query... │ Business logic  │
│  3   │ /test   │ Test syntax        │ type: syntax   │ Validate code   │
└──────┴─────────┴────────────────────┴────────────────┴─────────────────┘
```

**Columns:**
- **Step**: Execution order
- **Command**: CLI command to run
- **Description**: What this step does
- **Parameters**: Command arguments
- **Reason**: Why this step is needed

## Approval Process

After seeing the plan:

```
❓ 이 계획을 승인하시겠습니까?
계획 실행을 승인하시겠습니까? [Y/n]:
```

**Options:**
- Press `Y` or `Enter`: Approve and execute
- Press `N`: Reject the plan

## Execution

Once approved, steps execute sequentially:

```
▶ Step 1: Add schema file
✅ Step 1 완료

▶ Step 2: Create query
✅ Step 2 완료

▶ Step 3: Test syntax
✅ Step 3 완료
```

## Handling Failures

If a step fails:

```
❌ Step 2 실패

다음 조치를 선택하세요:
  1. 중단 (stop) - 전체 실행 중단
  2. 건너뛰기 (skip) - 이 단계를 건너뛰고 계속

선택 [stop/skip]:
```

**Options:**
- `stop`: Halt execution
- `skip`: Continue to next step

## Where Plans are Saved

Plans are automatically saved to:
```
.swmate/plans/plan_YYYYMMDD_HHMMSS.yaml
```

Example: `.swmate/plans/plan_20251209_143000.yaml`

## Common Use Cases

### 📊 Data Analysis
```bash
/architect "Analyze sales data and create monthly report query"
```

### 🐛 Debugging
```bash
/architect "Debug and fix the null pointer exception in user service"
```

### ✨ New Features
```bash
/architect "Implement password reset functionality with email notification"
```

### 🔧 Refactoring
```bash
/architect "Refactor the payment module to use the new API"
```

### 📝 Documentation
```bash
/architect "Generate API documentation for all endpoints"
```

## Safety Features

✅ **Approval Required**: Must approve plan before execution
✅ **Command Confirmation**: Shell commands ask for confirmation
✅ **Error Recovery**: Choose to stop or continue on errors
✅ **Full Logging**: All plans and results saved

## Tips for Best Results

1. **Be Specific**: "Create user authentication" vs "Add login"
2. **Mention Context**: Include file names, technologies, requirements
3. **State Expected Outcome**: "...that returns JSON response"
4. **Use Natural Language**: Write as you would explain to a colleague

## Troubleshooting

### Plan Generation Fails
**Problem**: "❌ LLM 응답을 받지 못했습니다"
**Solution**: Check your internet connection and try again

### Invalid JSON Error
**Problem**: "❌ JSON 파싱 오류"
**Solution**: Rephrase your request more clearly

### Step Execution Fails
**Problem**: Step keeps failing
**Solution**: Choose "stop", review the plan, and try a more specific request

## Next Steps

- Read [ARCHITECT_MODE_IMPLEMENTATION.md](ARCHITECT_MODE_IMPLEMENTATION.md) for detailed documentation
- Check [ARCHITECT_MODE.md](ARCHITECT_MODE.md) for architecture details
- Run `/help` for all available commands

## Keyboard Shortcuts

- `Ctrl+C`: Interrupt current operation
- `Ctrl+D`: Exit CLI
- `↑/↓`: Navigate command history

---

**Ready to start?** Just type `/architect "what you want to do"` and let the AI handle the rest! 🚀
