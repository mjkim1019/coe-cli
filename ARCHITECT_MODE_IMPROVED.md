# Architect Mode - Context-Aware Plan Generation

## What Changed? 🚀

The `/architect` command is now **context-aware** and more intelligent:

### Before ❌
- Always generated `/add` steps even for files already in session
- Wasted steps adding files that were already available
- Longer, less efficient plans

### After ✅
- Checks which files are already in session
- Only adds `/add` steps for NEW files
- Skips unnecessary file additions automatically
- More efficient, focused plans

## Recommended Workflow

### Step 1: Add Files First (Optional but Recommended)
```bash
# Add relevant files to provide context
/add schema/*.sql
/add models/*.py
/add config/*.yaml
```

**Why?** When you add files first:
- Architect mode knows what's available
- Plans are more focused and efficient
- No redundant `/add` steps
- Better understanding of your project

### Step 2: Use Architect Mode
```bash
/architect "Create a query to analyze customer subscriptions"
```

**What happens:**
1. ✅ Checks: Are schema files in session?
2. ✅ Result: Skips `/add schema.sql` - already available!
3. ✅ Focuses: Directly creates the query
4. ✅ Optimizes: Shows you what steps were skipped

## Examples

### Example 1: With Context (Recommended ✅)

```bash
# Step 1: Provide context
> /add schema/customers.sql
✓ Added 1 file

# Step 2: Request work
> /architect "Create query to find active customers"

📋 실행 계획 생성 중...
✓ 1개 파일이 이미 세션에 있습니다.
계획 생성 시 이 파일들을 활용합니다...

⚡ 1개 불필요한 단계를 최적화했습니다:
  - Step 1: Add customer schema (File 'customers.sql' already in session)

✅ 실행 계획이 생성되었습니다 (2개 단계).

┌──────┬─────────┬─────────────────────┬────────────┬──────────┐
│ Step │ Command │ Description         │ Parameters │ Reason   │
├──────┼─────────┼─────────────────────┼────────────┼──────────┤
│  1   │ /edit   │ Create query file   │ file: ...  │ Implement│
│  2   │ /test   │ Validate SQL syntax │ type: ...  │ Verify   │
└──────┴─────────┴─────────────────────┴────────────┴──────────┘
```

### Example 2: Without Context (Still Works)

```bash
# Direct request without files
> /architect "Create query to find active customers"

📋 실행 계획 생성 중...
💡 Tip: 파일을 먼저 추가하면 더 정확한 계획이 생성됩니다.
예: /add schema/*.sql 후 /architect 사용

✅ 실행 계획이 생성되었습니다 (3개 단계).

┌──────┬─────────┬─────────────────────┬────────────┬──────────┐
│ Step │ Command │ Description         │ Parameters │ Reason   │
├──────┼─────────┼─────────────────────┼────────────┼──────────┤
│  1   │ /add    │ Add customer schema │ file: ...  │ Need info│
│  2   │ /edit   │ Create query file   │ file: ...  │ Implement│
│  3   │ /test   │ Validate SQL syntax │ type: ...  │ Verify   │
└──────┴─────────┴─────────────────────┴────────────┴──────────┘
```

## Benefits

### 1. Efficiency ⚡
- Fewer steps in execution plan
- No redundant operations
- Faster execution

### 2. Intelligence 🧠
- Understands current context
- Makes smart decisions
- Avoids duplicate work

### 3. Clarity 📊
- Shows what was optimized
- Explains why steps were skipped
- Transparent decision-making

### 4. Flexibility 🔄
- Works with or without pre-added files
- Adapts to your workflow
- Gives helpful tips

## Best Practices

### ✅ Do This
```bash
# 1. Add relevant files first
/add schema/*.sql
/add models/*.py

# 2. Then use architect
/architect "your request"
```

### ⚠️ This Works Too (But Less Efficient)
```bash
# Direct use without context
/architect "your request"
# Will add files as needed, but less efficient
```

## Technical Details

### Smart Filtering Algorithm
1. LLM generates initial plan
2. System checks each `/add` step
3. Compares with files in session
4. Skips if file already exists
5. Renumbers remaining steps
6. Shows optimization summary

### Context Information
The system now provides detailed context to the LLM:
- Exact count of files in session
- Full list of available files (up to 10)
- Clear indication when no files are present
- Explicit instructions to avoid redundant steps

### Validation
- Checks file basenames and full paths
- Handles both single files and lists
- Preserves steps that add new files
- Only skips truly redundant operations

## Migration Guide

### For Existing Users
No changes needed! The feature is backward compatible:
- Old behavior: Still works (will add files as needed)
- New behavior: Automatically active when files are pre-added

### For New Users
Follow the recommended workflow:
1. Start CLI: `python run.py`
2. Add context: `/add relevant-files`
3. Use architect: `/architect "your request"`
4. Enjoy optimized plans! 🎉

## Example Session

```bash
$ python run.py

> /add schema/customers.sql schema/orders.sql
✓ Added 2 files

> /files
┌──────────────────────┐
│ Files in Session     │
├──────────────────────┤
│ customers.sql        │
│ orders.sql           │
└──────────────────────┘

> /architect "Create a query to find customers with orders in the last 30 days"

📋 실행 계획 생성 중...
✓ 2개 파일이 이미 세션에 있습니다.
계획 생성 시 이 파일들을 활용합니다...

⚡ 2개 불필요한 단계를 최적화했습니다:
  - Step 1: Add customer schema (File 'customers.sql' already in session)
  - Step 2: Add orders schema (File 'orders.sql' already in session)

✅ 실행 계획이 생성되었습니다 (2개 단계).

┌──────┬─────────┬──────────────────────────┬─────────────┬──────────┐
│ Step │ Command │ Description              │ Parameters  │ Reason   │
├──────┼─────────┼──────────────────────────┼─────────────┼──────────┤
│  1   │ /edit   │ Create customer query    │ file: q.sql │ Implement│
│  2   │ /test   │ Validate query syntax    │ type: sql   │ Verify   │
└──────┴─────────┴──────────────────────────┴─────────────┴──────────┘

❓ 이 계획을 승인하시겠습니까?
계획 실행을 승인하시겠습니까? [Y/n]: y

✅ 계획이 승인되었습니다.

🚀 계획 실행 시작

▶ Step 1: Create customer query
✅ Step 1 완료

▶ Step 2: Validate query syntax
✅ Step 2 완료

✅ 모든 단계가 성공적으로 완료되었습니다!
성공: 2, 실패: 0, 건너뛰기: 0

💾 계획이 저장되었습니다: .swmate/plans/plan_20251211_145230.yaml
```

## Summary

The improved Architect Mode is:
- **Smarter**: Checks context before planning
- **Faster**: Skips redundant operations
- **Clearer**: Shows what was optimized
- **Better**: Provides helpful tips

**Recommended**: Add files first, then use `/architect`! 🚀
