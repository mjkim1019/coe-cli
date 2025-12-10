# Architect Mode Implementation Guide

## Overview

Architect Mode is an AI Task Orchestration engine that automatically breaks down complex natural language requests into step-by-step execution plans, seeks user approval, and sequentially executes each step.

## Features Implemented

### ✅ Step 1: Plan Generation
- **LLM-based Plan Generation**: Uses GPT-4 to convert natural language requests into structured execution plans
- **JSON Format**: Plans are generated in a validated JSON format
- **Context-Aware**: Takes into account current session context (files in session, available resources)
- **Robust Error Handling**: Handles JSON parsing errors and malformed responses gracefully

### ✅ Step 2: Plan Visualization & Approval
- **Rich Table Display**: Plans are displayed in a beautiful, easy-to-read table format
- **Interactive Approval**: Users can approve or reject plans before execution
- **Detailed Information**: Shows command, description, parameters, and reasoning for each step

### ✅ Step 3: Sequential Execution Engine
- **Orchestration Logic**: Executes approved steps one by one in sequence
- **Result Recording**: Tracks success/failure status for each step
- **Error Handling**: On step failure, prompts user to:
  - **Stop**: Halt entire execution
  - **Skip**: Skip failed step and continue
  - (Future: Retry, Modify)
- **Command Execution**:
  - `/add`: Add files to session
  - `/edit`: Queue file modifications (simplified in v1)
  - `/exec`: Execute shell commands (with user confirmation)
  - `/test`: Run tests
  - `/ask`: Query LLM for information

### ✅ Step 4: State Saving
- **YAML Persistence**: Plans saved to `.swmate/plans/plan_YYYYMMDD_HHMMSS.yaml`
- **Full Traceability**: Saves plan metadata, all steps, and execution results
- **Load/Resume Support**: Can load previously saved plans (foundation for future /resume)

## Architecture

### Core Components

```
cli/core/
├── architect_mode.py         # Main orchestration engine
├── architect_plan.py          # Data structures (ExecutionPlan, ExecutionStep)
└── architect_prompts.py       # LLM prompts for plan generation
```

### Class Structure

#### `ArchitectMode`
Main orchestration engine with the following methods:
- `run(user_request)`: Main entry point
- `generate_plan(user_request)`: LLM-based plan generation
- `visualize_plan(plan)`: Display plan in rich table
- `approve_plan(plan)`: Get user approval
- `execute_plan(plan)`: Execute all steps sequentially
- `save_plan(plan)`: Save to YAML file
- `load_plan(plan_id)`: Load from YAML file
- `list_plans()`: List all saved plans

#### `ExecutionPlan`
Represents a complete execution plan:
- `plan_id`: Unique identifier (timestamp-based)
- `description`: User's original request
- `steps`: List of ExecutionStep objects
- `status`: pending, approved, executing, completed, failed, cancelled
- `results`: Execution results
- `save_to_file()`: Serialize to YAML
- `load_from_file()`: Deserialize from YAML

#### `ExecutionStep`
Represents a single step:
- `step_number`: Sequential number
- `command`: Command to execute (/add, /edit, etc.)
- `description`: Human-readable description
- `parameters`: Command parameters
- `reason`: Why this step is needed
- `status`: pending, executing, success, failed, skipped
- `output`: Execution output
- `error`: Error message if failed

## Usage

### Basic Usage

```bash
# Start Swing CLI
python run.py

# Use Architect Mode
/architect "Create a SQL query to calculate customer lifetime value"

# The system will:
# 1. Generate an execution plan
# 2. Display the plan in a table
# 3. Ask for your approval
# 4. Execute each step sequentially
# 5. Save the plan to .swmate/plans/
```

### Example Scenarios

#### Scenario 1: Text-to-SQL
```bash
/architect "유선 회선 기준으로 유무선 결합 가입년수 합산값 조회하는 쿼리 개발해줘"

# Expected plan:
# Step 1: /add - Add customer table schema
# Step 2: /add - Add subscription table schema
# Step 3: /edit - Create SQL query file
# Step 4: /test - Validate SQL syntax
```

#### Scenario 2: Feature Development
```bash
/architect "Create a user authentication API endpoint"

# Expected plan:
# Step 1: /add - Add existing API files for context
# Step 2: /edit - Create auth endpoint file
# Step 3: /edit - Add authentication middleware
# Step 4: /edit - Create test file
# Step 5: /test - Run unit tests
```

#### Scenario 3: Bug Fix
```bash
/architect "Fix memory leak in login.c file"

# Expected plan:
# Step 1: /add - Add login.c to session
# Step 2: /ask - Analyze code for memory leaks
# Step 3: /edit - Fix identified memory leaks
# Step 4: /exec - Compile the code
# Step 5: /test - Run memory leak tests
```

## File Structure

### Saved Plans

Plans are saved in YAML format:

```yaml
plan_id: "20251209_143000"
description: "Create SQL query for customer analysis"
created_at: "2025-12-09T14:30:00.123456"
status: "completed"
steps:
  - step_number: 1
    command: "/add"
    description: "Add customer schema"
    parameters:
      file: "schema/customer.sql"
    reason: "Need table structure for query"
    status: "success"
    output: "Added 1 file(s)"
    error: null
  - step_number: 2
    command: "/edit"
    description: "Create analysis query"
    parameters:
      file: "queries/customer_analysis.sql"
      action: "create query"
    reason: "Implement business logic"
    status: "success"
    output: "Edit operation queued: Create analysis query"
    error: null
results: []
```

## Integration with Existing Commands

The Architect Mode seamlessly integrates with existing Swing CLI commands:

- **`/add`**: File manager integration
- **`/edit`**: Uses existing edit infrastructure (simplified in v1)
- **`/ask`**: Uses LLM service with context manager
- **`/exec`**: Direct subprocess execution with safety checks
- **`/test`**: Foundation for test framework integration

## Safety Features

1. **User Approval Required**: Plans must be approved before execution
2. **Exec Confirmation**: Shell commands require explicit user confirmation
3. **Error Recovery**: Failed steps prompt user for action (stop/skip)
4. **Full Traceability**: All plans and results are saved

## Future Enhancements (P1)

- [ ] **Step-by-step Approval**: Approve individual steps instead of entire plan
- [ ] **Retry Mechanism**: Retry failed steps
- [ ] **Modify Step**: Edit step parameters before retry
- [ ] **Full Edit Integration**: Complete integration with edit coders
- [ ] **Resume Command**: `/resume <plan_id>` to continue interrupted plans
- [ ] **Plan Templates**: Save and reuse common plan patterns

## Future Enhancements (P2)

- [ ] **Parallel Execution**: Execute independent steps in parallel
- [ ] **Progress Bar**: Real-time progress visualization
- [ ] **Plan Validation**: Pre-execution validation of plan feasibility
- [ ] **Plan History**: Browse and search historical plans
- [ ] **Dry-run Mode**: Simulate execution without making changes

## Future Enhancements (P3)

- [ ] **Plan Optimization**: AI-suggested plan improvements
- [ ] **Export/Import**: Share plans between team members
- [ ] **Web UI**: Browser-based plan visualization and management
- [ ] **Performance Analytics**: Track execution time and resource usage

## Testing

Run the test suite:

```bash
python test_architect.py
```

This tests:
- ExecutionPlan creation and serialization
- YAML save/load functionality
- Step status tracking
- Prompt template formatting

## Troubleshooting

### Issue: JSON parsing error
**Solution**: The LLM may have returned invalid JSON. Try rephrasing your request more clearly.

### Issue: Plan execution stuck
**Solution**: If a step hangs, use Ctrl+C to interrupt, then choose "stop" when prompted.

### Issue: Files not added properly
**Solution**: Ensure file paths in the plan are correct and files exist.

## References

- [Architect Mode Specification](ARCHITECT_MODE.md)
- [Feature Roadmap](features_sepc_roadmap.md)
- [Main CLI Documentation](SWING_CLI_USAGE.md)

## Changelog

### v1.0.0 (2025-12-09)
- ✅ Initial implementation of Architect Mode
- ✅ Plan generation using GPT-4
- ✅ Rich table visualization
- ✅ Sequential execution engine
- ✅ YAML state persistence
- ✅ Integration with /add, /edit, /exec, /test, /ask commands
- ✅ Error handling and user interaction
- ✅ Test suite
