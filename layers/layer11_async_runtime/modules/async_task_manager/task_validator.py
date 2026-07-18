"""TaskValidator — Validate task configuration."""
from __future__ import annotations
from typing import Any, Dict, List
class TaskValidator:
    def __init__(self): self._results: List[Dict[str, Any]] = []
    def validate(self, config: Dict[str, Any]) -> Dict[str, Any]:
        errors = []
        if not config.get("name"): errors.append("name is required")
        if config.get("timeout", 0) <= 0: errors.append("timeout must be > 0")
        result = {"valid": len(errors) == 0, "errors": errors}
        self._results.append(result)
        return result
    def get_stats(self) -> Dict[str, Any]: return {"total": len(self._results)}
