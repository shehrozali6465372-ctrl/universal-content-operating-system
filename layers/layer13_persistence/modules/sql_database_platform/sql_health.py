"""sql_health.py — SQL platform health monitoring."""
from __future__ import annotations
import time
from typing import Any, Dict


class SQLHealth:
    """Monitors SQL platform health."""

    def __init__(self) -> None:
        self._checks: Dict[str, Dict[str, Any]] = {}
        self._last_check: float = 0.0

    def check(self, component: str, is_healthy: bool, latency_ms: float = 0.0,
              details: Dict[str, Any] = None) -> Dict[str, Any]:
        self._checks[component] = {"healthy": is_healthy, "latency_ms": latency_ms,
                                    "details": details or {}, "time": time.time()}
        self._last_check = time.time()
        return self._checks[component]

    def is_healthy(self) -> bool:
        if not self._checks:
            return True
        return all(c["healthy"] for c in self._checks.values())

    def get_component(self, component: str) -> Dict[str, Any]:
        return self._checks.get(component, {"healthy": False})

    def to_dict(self) -> Dict[str, Any]:
        return {"healthy": self.is_healthy(), "checks": dict(self._checks),
                "last_check": self._last_check}
