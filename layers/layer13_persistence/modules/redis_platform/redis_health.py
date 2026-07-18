"""redis_health.py — Redis health monitoring."""
from __future__ import annotations
import time
from typing import Any, Dict


class RedisHealth:
    """Monitors Redis health."""

    def __init__(self) -> None:
        self._checks: Dict[str, Dict[str, Any]] = {}
        self._last_check: float = 0.0

    def check(self, component: str, is_healthy: bool, latency_ms: float = 0.0) -> Dict[str, Any]:
        self._checks[component] = {"healthy": is_healthy, "latency_ms": latency_ms,
                                    "time": time.time()}
        self._last_check = time.time()
        return self._checks[component]

    def is_healthy(self) -> bool:
        if not self._checks:
            return True
        return all(c["healthy"] for c in self._checks.values())

    def to_dict(self) -> Dict[str, Any]:
        return {"healthy": self.is_healthy(), "checks": dict(self._checks)}
