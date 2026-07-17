"""System Health Monitor — Check overall system health."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional


class HealthCheck:
    """Result of a single health check."""

    __slots__ = ("component", "status", "latency_ms", "message", "timestamp")

    def __init__(self, component: str = "") -> None:
        self.component = component
        self.status: str = "unknown"
        self.latency_ms: float = 0.0
        self.message: str = ""
        self.timestamp: float = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "component": self.component,
            "status": self.status,
            "latency_ms": round(self.latency_ms, 1),
            "message": self.message,
        }


class SystemHealthMonitor:
    """Monitor system health across all components."""

    def __init__(self) -> None:
        self._checks: Dict[str, HealthCheck] = {}
        self._history: List[Dict[str, Any]] = []

    def register_component(self, name: str) -> None:
        if name not in self._checks:
            self._checks[name] = HealthCheck(name)

    def check(self, name: str, status: str = "healthy",
              latency_ms: float = 0.0, message: str = "") -> HealthCheck:
        if name not in self._checks:
            self._checks[name] = HealthCheck(name)
        check = self._checks[name]
        check.status = status
        check.latency_ms = latency_ms
        check.message = message
        check.timestamp = time.time()
        self._history.append(check.to_dict())
        return check

    def get_status(self, name: str) -> Optional[HealthCheck]:
        return self._checks.get(name)

    def get_all_status(self) -> Dict[str, str]:
        return {name: c.status for name, c in self._checks.items()}

    def get_overall_status(self) -> str:
        if not self._checks:
            return "unknown"
        statuses = [c.status for c in self._checks.values()]
        if all(s == "healthy" for s in statuses):
            return "healthy"
        if any(s == "critical" for s in statuses):
            return "critical"
        return "degraded"

    def get_alerts(self) -> List[Dict[str, Any]]:
        return [
            c.to_dict() for c in self._checks.values()
            if c.status in ("degraded", "critical")
        ]

    def get_diagnostics(self) -> Dict[str, Any]:
        return {
            "overall": self.get_overall_status(),
            "components": self.get_all_status(),
            "alert_count": len(self.get_alerts()),
            "history_size": len(self._history),
        }
