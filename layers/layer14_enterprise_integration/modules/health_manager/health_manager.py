"""HealthManager — unified health monitoring across all integration components."""
from __future__ import annotations
import time
from typing import Any, Callable, Dict, List, Optional
from enum import Enum


class HealthLevel(str, Enum):
    HEALTHY = "healthy"; DEGRADED = "degraded"; UNHEALTHY = "unhealthy"


class HealthCheck:
    __slots__ = ("name", "check_fn", "interval", "last_check", "last_result",
                 "consecutive_failures", "max_failures")

    def __init__(self, name: str, check_fn: Callable, interval: float = 60.0,
                 max_failures: int = 3) -> None:
        self.name = name
        self.check_fn = check_fn
        self.interval = interval
        self.last_check: float = 0.0
        self.last_result: Dict[str, Any] = {}
        self.consecutive_failures = 0
        self.max_failures = max_failures

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "last_check": self.last_check,
                "consecutive_failures": self.consecutive_failures}


class HealthManager:
    def __init__(self) -> None:
        self._checks: Dict[str, HealthCheck] = {}
        self._history: List[Dict[str, Any]] = []

    def register(self, name: str, check_fn: Callable, interval: float = 60.0,
                 max_failures: int = 3) -> HealthCheck:
        check = HealthCheck(name, check_fn, interval, max_failures)
        self._checks[name] = check
        return check

    def unregister(self, name: str) -> bool:
        if name in self._checks:
            del self._checks[name]
            return True
        return False

    def check(self, name: str) -> Dict[str, Any]:
        check = self._checks.get(name)
        if not check:
            return {"name": name, "status": HealthLevel.UNHEALTHY.value, "error": "not_registered"}
        try:
            result = check.check_fn()
            check.consecutive_failures = 0
            level = HealthLevel.HEALTHY if result.get("healthy", True) else HealthLevel.DEGRADED
            check.last_result = {"status": level.value, "details": result}
        except Exception as exc:
            check.consecutive_failures += 1
            level = HealthLevel.UNHEALTHY if check.consecutive_failures >= check.max_failures else HealthLevel.DEGRADED
            check.last_result = {"status": level.value, "error": str(exc)}
        check.last_check = time.time()
        entry = {"name": name, **check.last_result, "time": time.time()}
        self._history.append(entry)
        return entry

    def check_all(self) -> Dict[str, Any]:
        results = {}
        for name in self._checks:
            results[name] = self.check(name)
        statuses = [r.get("status") for r in results.values()]
        overall = HealthLevel.HEALTHY
        if HealthLevel.UNHEALTHY.value in statuses:
            overall = HealthLevel.UNHEALTHY
        elif HealthLevel.DEGRADED.value in statuses:
            overall = HealthLevel.DEGRADED
        return {"overall": overall.value, "checks": results,
                "total": len(results),
                "healthy": sum(1 for s in statuses if s == HealthLevel.HEALTHY.value)}

    def get_unhealthy(self) -> List[str]:
        return [name for name, check in self._checks.items()
                if check.consecutive_failures >= check.max_failures]

    def list_checks(self) -> List[Dict[str, Any]]:
        return [c.to_dict() for c in self._checks.values()]

    def get_history(self, name: Optional[str] = None) -> List[Dict[str, Any]]:
        if name:
            return [h for h in self._history if h.get("name") == name]
        return list(self._history)

    def count(self) -> int:
        return len(self._checks)
