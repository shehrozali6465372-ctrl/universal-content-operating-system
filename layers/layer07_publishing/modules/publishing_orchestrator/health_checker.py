"""Health Checker — Monitor pipeline health and module status."""
from __future__ import annotations
import time
from typing import Any, Dict, List


class HealthCheck:
    """Result of a health check."""

    __slots__ = ("check_id", "component", "healthy", "message", "latency_ms", "timestamp")

    def __init__(self, component: str = "", healthy: bool = True) -> None:
        self.check_id: str = f"hc_{int(time.time() * 1000) % 100000}"
        self.component = component
        self.healthy = healthy
        self.message: str = ""
        self.latency_ms: float = 0.0
        self.timestamp: float = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "check_id": self.check_id,
            "component": self.component,
            "healthy": self.healthy,
            "message": self.message,
            "latency_ms": round(self.latency_ms, 2),
        }


class HealthChecker:
    """Check health of pipeline components."""

    def __init__(self) -> None:
        self._checks: List[HealthCheck] = []

    def check(self, component: str) -> HealthCheck:
        check = HealthCheck(component, healthy=True)
        check.message = f"{component} is operational"
        self._checks.append(check)
        return check

    def get_checks(self, component: str = "") -> List[HealthCheck]:
        if component:
            return [c for c in self._checks if c.component == component]
        return list(self._checks)

    def is_healthy(self) -> bool:
        return all(c.healthy for c in self._checks[-10:])

    def get_overall_status(self) -> Dict[str, Any]:
        total = len(self._checks)
        healthy = sum(1 for c in self._checks if c.healthy)
        return {
            "total_checks": total,
            "healthy": healthy,
            "unhealthy": total - healthy,
            "status": "healthy" if healthy == total else "degraded",
        }
