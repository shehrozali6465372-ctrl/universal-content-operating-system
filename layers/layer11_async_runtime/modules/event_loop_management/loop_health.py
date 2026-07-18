"""LoopHealth — Loop health checking."""
from __future__ import annotations
import time
from typing import Any, Dict, List

class LoopHealth:
    def __init__(self) -> None:
        self._checks: List[Dict[str, Any]] = []
    def check(self, loop_id: str, is_healthy: bool = True, message: str = "OK") -> Dict[str, Any]:
        result = {"loop_id": loop_id, "healthy": is_healthy, "message": message, "time": time.time()}
        self._checks.append(result)
        return result
    def get_results(self) -> List[Dict[str, Any]]:
        return list(self._checks)
    def is_all_healthy(self) -> bool:
        return all(c["healthy"] for c in self._checks) if self._checks else True
    def get_stats(self) -> Dict[str, Any]:
        unhealthy = sum(1 for c in self._checks if not c["healthy"])
        return {"total": len(self._checks), "unhealthy": unhealthy}
