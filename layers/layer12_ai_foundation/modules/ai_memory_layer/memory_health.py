"""MemoryHealth — health monitoring for memory system."""
from __future__ import annotations

import time
from typing import Any, Dict, List


class MemoryHealth:
    """Health monitoring for the AI memory system."""

    def __init__(self) -> None:
        self._checks: Dict[str, bool] = {}
        self._start_time = time.time()

    def check(self, component: str, healthy: bool = True) -> None:
        self._checks[component] = healthy

    def is_healthy(self, component: str) -> bool:
        return self._checks.get(component, True)

    def get_unhealthy(self) -> List[str]:
        return [c for c, h in self._checks.items() if not h]

    def overall_health(self) -> Dict[str, Any]:
        total = len(self._checks)
        healthy = sum(1 for h in self._checks.values() if h)
        return {"total": total, "healthy": healthy,
                "unhealthy": total - healthy,
                "health_ratio": healthy / max(total, 1),
                "uptime": round(time.time() - self._start_time, 2)}
