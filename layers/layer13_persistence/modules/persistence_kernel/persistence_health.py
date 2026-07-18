"""persistence_health.py — Health monitoring."""
from __future__ import annotations
import time
from typing import Any, Dict


class PersistenceHealth:
    """Monitors health of persistence stores."""

    __slots__ = ("_checks", "_last_check", "_status")

    def __init__(self) -> None:
        self._checks: Dict[str, Dict[str, Any]] = {}
        self._last_check: float = 0.0
        self._status: str = "unknown"

    def check_store(self, name: str, is_healthy: bool, latency_ms: float = 0.0,
                    details: Dict[str, Any] = None) -> Dict[str, Any]:
        self._checks[name] = {"healthy": is_healthy, "latency_ms": latency_ms,
                               "details": details or {}, "checked_at": time.time()}
        self._last_check = time.time()
        self._recalculate_status()
        return self._checks[name]

    def _recalculate_status(self) -> None:
        if not self._checks:
            self._status = "unknown"
            return
        all_healthy = all(c["healthy"] for c in self._checks.values())
        self._status = "healthy" if all_healthy else "degraded"

    def mark_started(self) -> None:
        self._status = "healthy"

    def mark_stopped(self) -> None:
        self._status = "stopped"

    def get_store_health(self, name: str) -> Dict[str, Any]:
        return self._checks.get(name, {"healthy": False, "latency_ms": 0})

    def is_healthy(self) -> bool:
        return self._status == "healthy"

    def to_dict(self) -> Dict[str, Any]:
        return {"status": self._status, "checks": dict(self._checks),
                "last_check": self._last_check}

    def get_status(self, is_running: bool, stores: Dict[str, Any],
                   uptime: float) -> Dict[str, Any]:
        return {"running": is_running, "stores": len(stores),
                "uptime": uptime, "health": self._status,
                "last_check": self._last_check}
