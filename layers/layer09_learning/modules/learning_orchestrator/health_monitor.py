"""Health Monitor — Track module health and detect failures."""
from __future__ import annotations
import time
from typing import Any, Dict, Optional


class ModuleHealth:
    """Health status of a single module."""

    __slots__ = ("module_name", "status", "last_run_at", "success_count",
                 "failure_count", "avg_duration_ms", "last_error")

    def __init__(self, module_name: str = "") -> None:
        self.module_name = module_name
        self.status: str = "unknown"
        self.last_run_at: float = 0.0
        self.success_count: int = 0
        self.failure_count: int = 0
        self.avg_duration_ms: float = 0.0
        self.last_error: Optional[str] = None

    def record_success(self, duration_ms: float = 0.0) -> None:
        self.status = "healthy"
        self.success_count += 1
        self.last_run_at = time.time()
        if self.success_count == 1:
            self.avg_duration_ms = duration_ms
        else:
            self.avg_duration_ms = (self.avg_duration_ms * (self.success_count - 1) + duration_ms) / self.success_count

    def record_failure(self, error: str = "") -> None:
        self.status = "degraded"
        self.failure_count += 1
        self.last_run_at = time.time()
        self.last_error = error

    @property
    def is_healthy(self) -> bool:
        return self.status == "healthy"

    @property
    def total_runs(self) -> int:
        return self.success_count + self.failure_count

    def to_dict(self) -> Dict[str, Any]:
        return {
            "module_name": self.module_name,
            "status": self.status,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "avg_duration_ms": round(self.avg_duration_ms, 1),
            "total_runs": self.total_runs,
            "last_error": self.last_error,
        }


class HealthMonitor:
    """Monitor health of all learning modules."""

    def __init__(self) -> None:
        self._modules: Dict[str, ModuleHealth] = {}

    def register_module(self, module_name: str) -> ModuleHealth:
        if module_name not in self._modules:
            self._modules[module_name] = ModuleHealth(module_name)
        return self._modules[module_name]

    def record_success(self, module_name: str, duration_ms: float = 0.0) -> None:
        health = self.register_module(module_name)
        health.record_success(duration_ms)

    def record_failure(self, module_name: str, error: str = "") -> None:
        health = self.register_module(module_name)
        health.record_failure(error)

    def get_module_health(self, module_name: str) -> Optional[ModuleHealth]:
        return self._modules.get(module_name)

    def get_all_health(self) -> Dict[str, Dict[str, Any]]:
        return {name: h.to_dict() for name, h in self._modules.items()}

    def get_healthy_count(self) -> int:
        return sum(1 for h in self._modules.values() if h.is_healthy)

    def get_degraded_count(self) -> int:
        return sum(1 for h in self._modules.values() if h.status == "degraded")

    def get_overall_status(self) -> str:
        degraded = self.get_degraded_count()
        total = len(self._modules)
        if total == 0:
            return "unknown"
        if degraded == 0:
            return "healthy"
        if degraded < total * 0.3:
            return "degraded"
        return "critical"
