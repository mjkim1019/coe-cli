# Architect Mode - Cheat Sheet

## Quick Command Reference

```bash
# Basic Usage
/architect "your natural language request"

# Example: SQL Query
/architect "Create query to find active customers"

# Example: Bug Fix
/architect "Fix memory leak in auth module"

# Example: Feature
/architect "Add user profile API with validation"
```

## What It Does

1. **Generates Plan** - LLM creates step-by-step execution plan
2. **Shows Plan** - Displays in formatted table
3. **Gets Approval** - You approve/reject
4. **Executes** - Runs steps sequentially
5. **Saves** - Stores in `.swmate/plans/`

## Available Commands in Plans

| Command | Description | Example |
|---------|-------------|---------|
| `/add` | Add files to session | `file: schema.sql` |
| `/edit` | Modify/create files | `file: query.sql, action: create` |
| `/exec` | Run shell commands | `command: make test` |
| `/test` | Run tests | `type: syntax, file: query.sql` |
| `/ask` | Query LLM | `question: "explain this code"` |

## Plan Format

```
┌──────┬─────────┬──────────────┬────────────┬────────────┐
│ Step │ Command │ Description  │ Parameters │ Reason     │
├──────┼─────────┼──────────────┼────────────┼────────────┤
│  1   │ /add    │ Add schema   │ file: ...  │ Need info  │
│  2   │ /edit   │ Create query │ file: ...  │ Implement  │
│  3   │ /test   │ Validate     │ type: ...  │ Verify     │
└──────┴─────────┴──────────────┴────────────┴────────────┘
```

## User Interactions

### Approval
```
계획 실행을 승인하시겠습니까? [Y/n]: y
```

### On Failure
```
선택 [stop/skip]: 
  stop - Halt execution
  skip - Continue to next step
```

### Exec Confirmation
```
명령을 실행하시겠습니까? 'make test' [y/N]: y
```

## File Locations

Plans saved to:
```
.swmate/plans/plan_YYYYMMDD_HHMMSS.yaml
```

## Tips

✓ Be specific in requests
✓ Mention relevant files
✓ State expected outcomes
✓ Use natural language
✓ Review plan before approving

## Common Use Cases

**Data Analysis**
```bash
/architect "Analyze Q4 sales and create summary report"
```

**Debugging**
```bash
/architect "Find and fix null pointer in payment service"
```

**Feature Development**
```bash
/architect "Implement OAuth2 authentication with Google"
```

**Refactoring**
```bash
/architect "Refactor database layer to use connection pool"
```

**Testing**
```bash
/architect "Create comprehensive unit tests for API endpoints"
```

## Keyboard Shortcuts

- `Ctrl+C` - Interrupt
- `Ctrl+D` - Exit
- `↑/↓` - History

## Troubleshooting

| Issue | Solution |
|-------|----------|
| JSON parse error | Rephrase request more clearly |
| Step fails | Choose stop or skip |
| No LLM response | Check connection, retry |

## Get Help

```bash
/help                    # Show all commands
/architect              # See usage error message
```

## Documentation

- Quick Start: `docs/ARCHITECT_MODE_QUICKSTART.md`
- Full Guide: `docs/ARCHITECT_MODE_IMPLEMENTATION.md`
- Architecture: `docs/ARCHITECT_MODE.md`

---

**Quick Start**: `/architect "what you want"` and approve! 🚀
