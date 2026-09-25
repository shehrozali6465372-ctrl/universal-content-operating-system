"""Runtime health checks with strict contracts and bounded results."""
from __future__ import annotations

import inspect
import threading
import time
from typing import Callable, Dict, List, Optional


HealthCheckFn = Callable[[], bool]


class HealthCheck:
    """A single health check result."""

    __slots__ = ("name", "healthy", "message", "latency_ms", "checked_at")

    def __init__(self, name: str = "") -> None:
        self.name = name
        self.healthy = True
        self.message = "OK"
        self.latency_ms = 0.0
        self.checked_at = time.time()

    def to_dict(self) -> Dict[str, object]:
        return {
            "name": self.name,
            "healthy": self.healthy,
            "message": self.message,
            "latency_ms": round(self.latency_ms, 2),
            "checked_at": self.checked_at,
        }


class RuntimeHealth:
    """Thread-safe registry and executor for synchronous health checks."""

    def __init__(self, check_timeout: Optional[float] = None) -> None:
        if check_timeout is not None and (isinstance(check_timeout, bool) or not isinstance(check_timeout, (int, float)) or check_timeout <= 0):
            raise ValueError("check_timeout must be > 0")
        self._checks: Dict[str, HealthCheckFn] = {}
        self._results: List[HealthCheck] = []
        self._lock = threading.RLock()
        self._check_timeout = check_timeout

    def register_check(self, name: str, check_fn: HealthCheckFn) -> None:
        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty string")
        if inspect.iscoroutinefunction(check_fn) or not callable(check_fn):
            raise TypeError("check_fn must be a synchronous callable")
        with self._lock:
            self._checks[name] = check_fn

    def run_checks(self) -> List[HealthCheck]:
        with self._lock:
            checks = list(self._checks.items())
        results: List[HealthCheck] = []
        for name, check_fn in checks:
            start = time.monotonic()
            result = HealthCheck(name)
            try:
                healthy = check_fn()
                if not isinstance(healthy, bool):
                    raise TypeError("health check must return bool")
                if self._check_timeout is not None and time.monotonic() - start > self._check_timeout:
                    raise TimeoutError(f"health check exceeded {self._check_timeout}s")
                result.healthy = healthy
                result.message = "OK" if healthy else "FAIL"
            except Exception:
                result.healthy = False
                result.message = "health check failed"
            result.latency_ms = max(0.0, (time.monotonic() - start) * 1000)
            results.append(result)
        with self._lock:
            self._results = results
        return list(results)

    def is_healthy(self) -> bool:
        with self._lock:
            if not self._results:
                return False if self._checks else True
            return all(result.healthy for result in self._results)

    def get_results(self) -> List[HealthCheck]:
        with self._lock:
            return list(self._results)

    def get_unhealthy(self) -> List[HealthCheck]:
        with self._lock:
            return [result for result in self._results if not result.healthy]

    def get_stats(self) -> Dict[str, object]:
        with self._lock:
            return {
                "total_checks": len(self._checks),
                "last_run_count": len(self._results),
                "healthy": self.is_healthy(),
            }
