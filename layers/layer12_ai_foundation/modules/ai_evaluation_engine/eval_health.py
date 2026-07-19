"""EvalHealth — health monitoring."""
from __future__ import annotations
import time
from typing import Any, Dict, List

class EvalHealth:
    def __init__(self) -> None:
        self._checks: Dict[str, bool] = {}; self._start = time.time()
    def check(self, component: str, healthy: bool = True) -> None: self._checks[component] = healthy
    def is_healthy(self, component: str) -> bool: return self._checks.get(component, True)
    def get_unhealthy(self) -> List[str]: return [c for c, h in self._checks.items() if not h]
    def overall_health(self) -> Dict[str, Any]:
        t = len(self._checks); h = sum(1 for v in self._checks.values() if v)
        return {"total": t, "healthy": h, "uptime": round(time.time() - self._start, 2)}
