"""database_health.py — Database health monitoring."""
from __future__ import annotations
import time
from typing import Any, Dict


class DatabaseHealth:
    """Monitors database health."""

    def __init__(self) -> None:
        self._checks: Dict[str, Dict[str, Any]] = {}
        self._last_check: float = 0.0

    def check(self, component: str, is_healthy: bool, latency_ms: float = 0.0,
              details: Dict[str, Any] = None) -> Dict[str, Any]:
        result = {"healthy": is_healthy, "latency_ms": latency_ms,
                  "details": details or {}, "time": time.time()}
        self._checks[component] = result
        self._last_check = time.time()
        return result

    def is_healthy(self) -> bool:
        if not self._checks:
            return True
        return all(c["healthy"] for c in self._checks.values())

    def get_component(self, component: str) -> Dict[str, Any]:
        return self._checks.get(component, {"healthy": False})

    def to_dict(self) -> Dict[str, Any]:
        return {"healthy": self.is_healthy(), "checks": len(self._checks),
                "last_check": self._last_check}
