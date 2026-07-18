"""PromptHealth — health monitoring for prompt system."""
from __future__ import annotations

import time
from typing import Any, Dict


class PromptHealth:
    """Health monitoring for the prompt intelligence system."""

    def __init__(self) -> None:
        self._start_time = time.time()
        self._checks: Dict[str, bool] = {}

    def check(self, component: str, is_healthy: bool = True) -> Dict[str, Any]:
        self._checks[component] = is_healthy
        return {"component": component, "healthy": is_healthy, "time": time.time()}

    def is_healthy(self, component: str) -> bool:
        return self._checks.get(component, True)

    def get_unhealthy(self) -> list:
        return [c for c, h in self._checks.items() if not h]

    def overall_health(self) -> Dict[str, Any]:
        total = len(self._checks)
        healthy = sum(1 for h in self._checks.values() if h)
        return {"total": total, "healthy": healthy,
                "unhealthy": total - healthy,
                "health_ratio": healthy / max(total, 1),
                "uptime": round(time.time() - self._start_time, 2)}
