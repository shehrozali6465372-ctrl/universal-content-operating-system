"""health_coordinator.py — Health coordination."""
from __future__ import annotations
import time
from typing import Any, Dict


class HealthCoordinator:
    """Coordinates health checks across all stores."""

    def __init__(self) -> None:
        self._checks: Dict[str, Dict[str, Any]] = {}
        self._last_check: float = 0.0

    def check(self, store_name: str, is_healthy: bool, latency_ms: float = 0.0) -> Dict[str, Any]:
        result = {"healthy": is_healthy, "latency_ms": latency_ms, "time": time.time()}
        self._checks[store_name] = result
        self._last_check = time.time()
        return result

    def is_healthy(self) -> bool:
        if not self._checks:
            return True
        return all(c["healthy"] for c in self._checks.values())

    def get_store_health(self, store_name: str) -> Dict[str, Any]:
        return self._checks.get(store_name, {"healthy": False})

    def stats(self) -> Dict[str, Any]:
        return {"stores_checked": len(self._checks), "healthy": self.is_healthy()}
