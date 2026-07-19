"""AIPolicy — enforce orchestrator policies."""
from __future__ import annotations
from typing import Any, Dict, List

class AIPolicy:
    def __init__(self) -> None:
        self._policies: Dict[str, Any] = {"max_retries": 3, "timeout": 30}
    def set(self, key: str, value: Any) -> None: self._policies[key] = value
    def get(self, key: str, default: Any = None) -> Any: return self._policies.get(key, default)
    def check(self, operation: str, params: Dict[str, Any] | None = None) -> Dict[str, Any]:
        violations: List[str] = []
        params = params or {}
        if params.get("retries", 0) > self._policies.get("max_retries", 3):
            violations.append("Max retries exceeded")
        return {"allowed": len(violations) == 0, "violations": violations}
    def to_dict(self) -> Dict[str, Any]: return dict(self._policies)
