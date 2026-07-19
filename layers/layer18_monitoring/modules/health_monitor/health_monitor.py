"""HealthMonitor — continuous health monitoring with alerts."""
from __future__ import annotations
import time
from typing import Any, Callable, Dict, List, Optional
from enum import Enum


class HealthLevel(str, Enum):
    HEALTHY = "healthy"; DEGRADED = "degraded"; UNHEALTHY = "unhealthy"


class HealthCheck:
    __slots__ = ("name", "check_fn", "interval", "last_check", "consecutive_failures",
                 "max_failures", "timeout", "metadata")

    def __init__(self, name: str, check_fn: Callable, interval: float = 60.0,
                 max_failures: int = 3, timeout: float = 5.0) -> None:
        self.name = name
        self.check_fn = check_fn
        self.interval = interval
        self.last_check: float = 0.0
        self.consecutive_failures = 0
        self.max_failures = max_failures
        self.timeout = timeout
        self.metadata: Dict[str, Any] = {}


class HealthMonitor:
    def __init__(self) -> None:
        self._checks: Dict[str, HealthCheck] = {}
        self._results: Dict[str, Dict[str, Any]] = {}
        self._history: List[Dict[str, Any]] = []

    def register(self, name: str, check_fn: Callable, interval: float = 60.0,
                 max_failures: int = 3) -> HealthCheck:
        check = HealthCheck(name, check_fn, interval, max_failures)
        self._checks[name] = check
        return check

    def unregister(self, name: str) -> bool:
        if name in self._checks:
            del self._checks[name]
            self._results.pop(name, None)
            return True
        return False

    def check(self, name: str) -> Dict[str, Any]:
        check = self._checks.get(name)
        if not check:
            return {"name": name, "status": HealthLevel.UNHEALTHY.value, "error": "not_found"}
        try:
            result = check.check_fn()
            healthy = result.get("healthy", True) if isinstance(result, dict) else bool(result)
            level = HealthLevel.HEALTHY if healthy else HealthLevel.DEGRADED
            check.consecutive_failures = 0
        except Exception as exc:
            check.consecutive_failures += 1
            level = HealthLevel.UNHEALTHY if check.consecutive_failures >= check.max_failures else HealthLevel.DEGRADED
            result = {"error": str(exc)}
        check.last_check = time.time()
        entry = {"name": name, "status": level.value, "details": result,
                 "failures": check.consecutive_failures, "time": time.time()}
        self._results[name] = entry
        self._history.append(entry)
        return entry

    def check_all(self) -> Dict[str, Any]:
        results = {name: self.check(name) for name in self._checks}
        statuses = [r["status"] for r in results.values()]
        overall = HealthLevel.HEALTHY
        if HealthLevel.UNHEALTHY.value in statuses:
            overall = HealthLevel.UNHEALTHY
        elif HealthLevel.DEGRADED.value in statuses:
            overall = HealthLevel.DEGRADED
        return {"overall": overall.value, "checks": results}

    def get_unhealthy(self) -> List[str]:
        return [name for name, r in self._results.items()
                if r["status"] == HealthLevel.UNHEALTHY.value]

    def list_checks(self) -> List[str]:
        return list(self._checks.keys())

    def get_history(self, name: Optional[str] = None) -> List[Dict[str, Any]]:
        if name:
            return [h for h in self._history if h.get("name") == name]
        return list(self._history)

    def count(self) -> int:
        return len(self._checks)
