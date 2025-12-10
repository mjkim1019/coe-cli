# 🚀 Quick Start - Try It Now!

Want to see Architect Mode in action? Follow these 3 simple steps:

## Step 1: Start the CLI (30 seconds)

```bash
cd /home/tungdv15/coe-cli
python run.py
```

You'll see the Swing CLI welcome screen.

## Step 2: Run Your First Architect Command (1 minute)

Copy and paste this command:

```bash
/architect "Create a SQL query to find customers with subscriptions longer than 3 years, include subscription duration calculation"
```

## Step 3: Watch the Magic! ✨

You'll see:

1. **Plan Generation** (5 seconds)
   - AI analyzes your request
   - Generates step-by-step plan

2. **Plan Display** (you see it)
   ```
   ┌──────┬─────────┬──────────────────────┬────────────┬──────────────┐
   │ Step │ Command │ Description          │ Parameters │ Reason       │
   └──────┴─────────┴──────────────────────┴────────────┴──────────────┘
   ```

3. **Approval Prompt**
   ```
   계획 실행을 승인하시겠습니까? [Y/n]:
   ```
   **Just press Enter!**

4. **Execution** (10 seconds)
   - Watch each step execute
   - See checkmarks ✅ as steps complete

5. **Results**
   ```
   ✅ All steps completed!
   💾 Plan saved to: .swmate/plans/plan_YYYYMMDD_HHMMSS.yaml
   ```

## What Just Happened?

The AI automatically:
- ✅ Analyzed your request
- ✅ Created a multi-step execution plan
- ✅ Got your approval
- ✅ Executed each step
- ✅ Saved everything for later reference

**Total time: ~1 minute**

## Try More Examples

### Example 1: Simple Query
```bash
/architect "Create a query to list all active customers"
```

### Example 2: Analysis
```bash
/architect "Analyze customer data and create a monthly subscription report"
```

### Example 3: Korean
```bash
/architect "고객 정보를 분석해서 월별 구독 통계 리포트 만들어줘"
```

### Example 4: Complex Task
```bash
/architect "Create a comprehensive customer analytics package with queries for retention analysis, churn prediction, and revenue forecasting"
```

## View Your Results

All plans are saved in:
```bash
ls -la .swmate/plans/
cat .swmate/plans/plan_*.yaml  # View the latest plan
```

## Tips

💡 **Be specific** - The more details you provide, the better the plan
�� **Use natural language** - Write as you would talk to a colleague
💡 **Review before approving** - Check the plan makes sense
💡 **Experiment** - Try different types of requests!

## Need Help?

```bash
/help          # See all commands
/architect     # See usage instructions
```

Or read:
- [Complete Walkthrough](README.md)
- [Quick Reference](../../ARCHITECT_MODE_CHEATSHEET.md)

---

**Ready? Just 3 steps: Start CLI → Type `/architect "..."` → Press Enter!** 🎉
