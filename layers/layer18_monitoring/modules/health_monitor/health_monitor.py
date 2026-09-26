"""Bounded health checks with timeout handling."""
from __future__ import annotations

import threading
import time
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class HealthLevel(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class HealthCheck:
    __slots__ = (
        "name", "check_fn", "interval", "last_check", "consecutive_failures",
        "max_failures", "timeout", "metadata",
    )

    def __init__(
        self,
        name: str,
        check_fn: Callable[[], Any],
        interval: float = 60.0,
        max_failures: int = 3,
        timeout: float = 5.0,
    ) -> None:
        if not name.strip() or interval < 0 or max_failures <= 0 or timeout <= 0:
            raise ValueError("invalid health check configuration")
        self.name = name
        self.check_fn = check_fn
        self.interval = interval
        self.last_check = 0.0
        self.consecutive_failures = 0
        self.max_failures = max_failures
        self.timeout = timeout
        self.metadata: Dict[str, Any] = {}


class HealthMonitor:
    def __init__(self, history_size: int = 1000) -> None:
        if history_size <= 0:
            raise ValueError("history_size must be positive")
        self._lock = threading.RLock()
        self._history_size = history_size
        self._checks: Dict[str, HealthCheck] = {}
        self._results: Dict[str, Dict[str, Any]] = {}
        self._history: List[Dict[str, Any]] = []

    def register(
        self,
        name: str,
        check_fn: Callable[[], Any],
        interval: float = 60.0,
        max_failures: int = 3,
        timeout: float = 5.0,
    ) -> HealthCheck:
        check = HealthCheck(name, check_fn, interval, max_failures, timeout)
        with self._lock:
            self._checks[name] = check
        return check

    def unregister(self, name: str) -> bool:
        with self._lock:
            self._results.pop(name, None)
            return self._checks.pop(name, None) is not None

    def check(self, name: str) -> Dict[str, Any]:
        with self._lock:
            check = self._checks.get(name)
        if check is None:
            return {
                "name": name,
                "status": HealthLevel.UNHEALTHY.value,
                "error": "not_found",
            }

        result_holder: Dict[str, Any] = {}
        error_holder: List[BaseException] = []
        done = threading.Event()

        def run_check() -> None:
            try:
                result_holder["value"] = check.check_fn()
            except BaseException as exc:
                error_holder.append(exc)
            finally:
                done.set()

        worker = threading.Thread(
            target=run_check, name=f"health-check-{name}", daemon=True
        )
        worker.start()
        timed_out = not done.wait(check.timeout)

        if timed_out:
            result: Any = {
                "error": f"health check timed out after {check.timeout:.2f}s"
            }
        elif error_holder:
            result = {"error": str(error_holder[0])}
        else:
            result = result_holder.get("value")

        with self._lock:
            failed = timed_out or (
                isinstance(result, dict) and "error" in result
            )
            check.consecutive_failures = (
                check.consecutive_failures + 1 if failed else 0
            )
            failures = check.consecutive_failures

        if failed:
            status = (
                HealthLevel.UNHEALTHY
                if failures >= check.max_failures
                else HealthLevel.DEGRADED
            )
        else:
            healthy = (
                result.get("healthy", True)
                if isinstance(result, dict)
                else bool(result)
            )
            status = HealthLevel.HEALTHY if healthy else HealthLevel.DEGRADED

        now = time.time()
        entry = {
            "name": name,
            "status": status.value,
            "details": result,
            "failures": failures,
            "time": now,
        }
        with self._lock:
            check.last_check = now
            self._results[name] = entry
            self._history.append(dict(entry))
            if len(self._history) > self._history_size:
                del self._history[:-self._history_size]
        return entry

    def check_all(self) -> Dict[str, Any]:
        with self._lock:
            names = list(self._checks)
        results = {name: self.check(name) for name in names}
        statuses = [result["status"] for result in results.values()]
        overall = (
            HealthLevel.UNHEALTHY.value
            if "unhealthy" in statuses
            else HealthLevel.DEGRADED.value
            if "degraded" in statuses
            else HealthLevel.HEALTHY.value
        )
        return {"overall": overall, "checks": results}

    def get_unhealthy(self) -> List[str]:
        with self._lock:
            return [
                name
                for name, result in self._results.items()
                if result["status"] == HealthLevel.UNHEALTHY.value
            ]

    def list_checks(self) -> List[str]:
        with self._lock:
            return list(self._checks)

    def get_history(self, name: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._lock:
            values = (
                self._history
                if name is None
                else [entry for entry in self._history if entry["name"] == name]
            )
            return [dict(value) for value in values]

    def count(self) -> int:
        with self._lock:
            return len(self._checks)
