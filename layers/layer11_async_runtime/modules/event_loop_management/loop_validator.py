"""LoopValidator — Validate loop configuration."""
from __future__ import annotations
from typing import Any, Dict, List

class LoopValidator:
    def __init__(self) -> None:
        self._results: List[Dict[str, Any]] = []
    def validate(self, config: Dict[str, Any]) -> Dict[str, Any]:
        errors = []
        if config.get("max_loops", 0) < 1:
            errors.append("max_loops must be >= 1")
        result = {"valid": len(errors) == 0, "errors": errors}
        self._results.append(result)
        return result
    def get_stats(self) -> Dict[str, Any]:
        return {"total": len(self._results)}
