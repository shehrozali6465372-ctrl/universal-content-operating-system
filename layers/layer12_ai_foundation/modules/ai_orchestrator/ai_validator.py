"""AIValidator — validate orchestrator inputs."""
from __future__ import annotations
from typing import Any, Dict, List

class AIValidator:
    def validate_task(self, name: str, input_data: Dict[str, Any] | None = None) -> Dict[str, Any]:
        issues: List[str] = []
        if not name or not name.strip(): issues.append("Empty task name")
        return {"valid": len(issues) == 0, "issues": issues}
    def validate_pipeline(self, name: str, steps: List[str] | None = None) -> Dict[str, Any]:
        issues: List[str] = []
        if not name: issues.append("Empty pipeline name")
        if steps is not None and len(steps) == 0: issues.append("Empty steps list")
        return {"valid": len(issues) == 0, "issues": issues}
    def validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        issues: List[str] = []
        if config.get("max_concurrent", 0) < 1: issues.append("Invalid max_concurrent")
        return {"valid": len(issues) == 0, "issues": issues}
