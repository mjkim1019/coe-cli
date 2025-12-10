"""
Architect Plan Data Structures
Defines the ExecutionPlan class for storing and managing execution plans
"""

import json
import yaml
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path


class ExecutionStep:
    """Represents a single step in an execution plan"""
    
    def __init__(self, step_number: int, command: str, description: str, 
                 parameters: Dict[str, Any], reason: str):
        self.step_number = step_number
        self.command = command
        self.description = description
        self.parameters = parameters
        self.reason = reason
        self.status = "pending"  # pending, executing, success, failed, skipped
        self.output = None
        self.error = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert step to dictionary"""
        return {
            "step_number": self.step_number,
            "command": self.command,
            "description": self.description,
            "parameters": self.parameters,
            "reason": self.reason,
            "status": self.status,
            "output": self.output,
            "error": self.error
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExecutionStep':
        """Create step from dictionary"""
        step = cls(
            step_number=data["step_number"],
            command=data["command"],
            description=data["description"],
            parameters=data["parameters"],
            reason=data["reason"]
        )
        step.status = data.get("status", "pending")
        step.output = data.get("output")
        step.error = data.get("error")
        return step


class ExecutionPlan:
    """Represents a complete execution plan with all steps"""
    
    def __init__(self, plan_id: str, description: str, steps: List[ExecutionStep]):
        self.plan_id = plan_id
        self.description = description
        self.steps = steps
        self.created_at = datetime.now()
        self.status = "pending"  # pending, approved, executing, completed, failed, cancelled
        self.results = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert plan to dictionary"""
        return {
            "plan_id": self.plan_id,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "status": self.status,
            "steps": [step.to_dict() for step in self.steps],
            "results": self.results
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExecutionPlan':
        """Create plan from dictionary"""
        steps = [ExecutionStep.from_dict(step_data) for step_data in data["steps"]]
        plan = cls(
            plan_id=data["plan_id"],
            description=data["description"],
            steps=steps
        )
        plan.created_at = datetime.fromisoformat(data["created_at"])
        plan.status = data.get("status", "pending")
        plan.results = data.get("results", [])
        return plan
    
    def save_to_file(self, filepath: Path):
        """Save plan to YAML file"""
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            yaml.dump(self.to_dict(), f, allow_unicode=True, sort_keys=False)
    
    @classmethod
    def load_from_file(cls, filepath: Path) -> 'ExecutionPlan':
        """Load plan from YAML file"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        return cls.from_dict(data)
    
    def get_step_by_number(self, step_number: int) -> Optional[ExecutionStep]:
        """Get a specific step by its number"""
        for step in self.steps:
            if step.step_number == step_number:
                return step
        return None
    
    def mark_step_status(self, step_number: int, status: str, output: str = None, error: str = None):
        """Update step status"""
        step = self.get_step_by_number(step_number)
        if step:
            step.status = status
            step.output = output
            step.error = error
    
    def get_next_pending_step(self) -> Optional[ExecutionStep]:
        """Get the next step that is pending execution"""
        for step in self.steps:
            if step.status == "pending":
                return step
        return None
    
    def is_complete(self) -> bool:
        """Check if all steps are complete (success, failed, or skipped)"""
        for step in self.steps:
            if step.status in ["pending", "executing"]:
                return False
        return True
    
    def get_summary(self) -> Dict[str, int]:
        """Get summary of step statuses"""
        summary = {
            "total": len(self.steps),
            "success": 0,
            "failed": 0,
            "skipped": 0,
            "pending": 0
        }
        for step in self.steps:
            if step.status == "success":
                summary["success"] += 1
            elif step.status == "failed":
                summary["failed"] += 1
            elif step.status == "skipped":
                summary["skipped"] += 1
            elif step.status == "pending":
                summary["pending"] += 1
        return summary
