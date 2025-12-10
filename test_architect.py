#!/usr/bin/env python
"""
Test script for Architect Mode
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from cli.core.architect_plan import ExecutionPlan, ExecutionStep
from pathlib import Path
import json

def test_execution_plan():
    """Test ExecutionPlan creation and serialization"""
    print("Testing ExecutionPlan...")
    
    # Create some steps
    steps = [
        ExecutionStep(
            step_number=1,
            command="/add",
            description="Add schema file",
            parameters={"file": "schema.sql"},
            reason="Need table structure"
        ),
        ExecutionStep(
            step_number=2,
            command="/edit",
            description="Create query",
            parameters={"file": "query.sql", "action": "create query"},
            reason="Implement business logic"
        )
    ]
    
    # Create plan
    plan = ExecutionPlan(
        plan_id="test_001",
        description="Test plan",
        steps=steps
    )
    
    # Test to_dict
    plan_dict = plan.to_dict()
    print(f"✅ Plan dictionary created: {len(plan_dict)} keys")
    
    # Test from_dict
    plan_restored = ExecutionPlan.from_dict(plan_dict)
    print(f"✅ Plan restored from dict: {len(plan_restored.steps)} steps")
    
    # Test save/load
    test_file = Path("/tmp/test_plan.yaml")
    plan.save_to_file(test_file)
    print(f"✅ Plan saved to: {test_file}")
    
    plan_loaded = ExecutionPlan.load_from_file(test_file)
    print(f"✅ Plan loaded from file: {plan_loaded.plan_id}")
    
    # Test step operations
    plan.mark_step_status(1, "success", output="File added")
    plan.mark_step_status(2, "failed", error="Syntax error")
    
    summary = plan.get_summary()
    print(f"✅ Summary: {summary}")
    
    # Clean up
    test_file.unlink()
    print("\n✅ All ExecutionPlan tests passed!")
    return True

def test_prompts():
    """Test prompt templates"""
    print("\nTesting Architect Prompts...")
    
    from cli.core.architect_prompts import ArchitectPrompts
    
    prompts = ArchitectPrompts()
    
    # Test system prompt
    assert len(prompts.PLAN_GENERATION_SYSTEM) > 0
    print("✅ System prompt loaded")
    
    # Test user template
    user_msg = prompts.PLAN_GENERATION_USER_TEMPLATE.format(
        user_request="Create a SQL query",
        files_count=5,
        file_list="file1.py, file2.py"
    )
    assert "Create a SQL query" in user_msg
    print("✅ User template formatted correctly")
    
    print("\n✅ All Prompt tests passed!")
    return True

if __name__ == "__main__":
    try:
        test_execution_plan()
        test_prompts()
        print("\n🎉 All tests passed successfully!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
