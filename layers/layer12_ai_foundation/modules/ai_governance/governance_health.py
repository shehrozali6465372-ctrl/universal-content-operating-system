"""GovernanceHealth — health monitoring."""
from __future__ import annotations
import time
from typing import Any, Dict

class GovernanceHealth:
    def __init__(self) -> None:
        self._checks: Dict[str, bool] = {}; self._start = time.time()
    def check(self, comp: str, healthy: bool = True) -> None: self._checks[comp] = healthy
    def is_healthy(self, comp: str) -> bool: return self._checks.get(comp, True)
    def overall_health(self) -> Dict[str, Any]:
        t = len(self._checks); h = sum(1 for v in self._checks.values() if v)
        return {"total": t, "healthy": h, "uptime": round(time.time() - self._start, 2)}
