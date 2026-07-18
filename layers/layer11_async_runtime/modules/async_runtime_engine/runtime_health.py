"""RuntimeHealth — Health checking for the runtime."""
from __future__ import annotations
import time
from typing import Any, Dict, List


class HealthCheck:
    """A single health check result."""
    __slots__ = ("name", "healthy", "message", "latency_ms", "checked_at")

    def __init__(self, name: str = "") -> None:
        self.name = name
        self.healthy: bool = True
        self.message: str = "OK"
        self.latency_ms: float = 0.0
        self.checked_at: float = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "healthy": self.healthy,
                "message": self.message, "latency_ms": round(self.latency_ms, 2)}


class RuntimeHealth:
    """Runtime health monitoring with configurable checks."""

    def __init__(self) -> None:
        self._checks: Dict[str, Any] = {}
        self._results: List[HealthCheck] = []

    def register_check(self, name: str, check_fn: Any) -> None:
        self._checks[name] = check_fn

    def run_checks(self) -> List[HealthCheck]:
        results = []
        for name, check_fn in self._checks.items():
            start = time.time()
            hc = HealthCheck(name)
            try:
                hc.healthy = check_fn()
                hc.message = "OK" if hc.healthy else "FAIL"
            except Exception as e:
                hc.healthy = False
                hc.message = str(e)
            hc.latency_ms = (time.time() - start) * 1000
            results.append(hc)
        self._results = results
        return results

    def is_healthy(self) -> bool:
        if not self._results:
            return True
        return all(r.healthy for r in self._results)

    def get_results(self) -> List[HealthCheck]:
        return list(self._results)

    def get_unhealthy(self) -> List[HealthCheck]:
        return [r for r in self._results if not r.healthy]

    def get_stats(self) -> Dict[str, Any]:
        return {"total_checks": len(self._checks),
                "last_run_count": len(self._results),
                "healthy": self.is_healthy()}
