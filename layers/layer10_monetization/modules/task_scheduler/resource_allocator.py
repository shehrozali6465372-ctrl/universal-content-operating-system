"""Resource Allocator — Allocate system resources to tasks."""
from __future__ import annotations
from typing import Any, Dict, Optional


class ResourcePool:
    """Available system resources."""

    def __init__(self) -> None:
        self.cpu_cores: float = 8.0
        self.memory_gb: float = 16.0
        self.gpu_count: int = 0
        self.api_quota: int = 1000
        self.worker_slots: int = 10

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cpu_cores": self.cpu_cores,
            "memory_gb": self.memory_gb,
            "gpu_count": self.gpu_count,
            "api_quota": self.api_quota,
            "worker_slots": self.worker_slots,
        }


class ResourceAllocator:
    """Allocate and track resources for task execution."""

    def __init__(self, pool: Optional[ResourcePool] = None) -> None:
        self._pool = pool or ResourcePool()
        self._allocated: Dict[str, Dict[str, float]] = {}
        self._total_allocated: Dict[str, float] = {
            "cpu": 0.0, "memory": 0.0, "gpu": 0, "api": 0, "workers": 0,
        }

    def allocate(self, task_id: str, resources: Dict[str, float]) -> bool:
        if self._can_allocate(resources):
            for key, amount in resources.items():
                self._total_allocated[key] = self._total_allocated.get(key, 0) + amount
            self._allocated[task_id] = dict(resources)
            return True
        return False

    def release(self, task_id: str) -> bool:
        resources = self._allocated.pop(task_id, None)
        if resources:
            for key, amount in resources.items():
                self._total_allocated[key] = max(0, self._total_allocated.get(key, 0) - amount)
            return True
        return False

    def available(self, resource: str = "") -> float:
        if resource == "cpu":
            return max(0, self._pool.cpu_cores - self._total_allocated.get("cpu", 0))
        elif resource == "memory":
            return max(0, self._pool.memory_gb - self._total_allocated.get("memory", 0))
        elif resource == "gpu":
            return max(0, self._pool.gpu_count - int(self._total_allocated.get("gpu", 0)))
        elif resource == "api":
            return max(0, self._pool.api_quota - int(self._total_allocated.get("api", 0)))
        elif resource == "workers":
            return max(0, self._pool.worker_slots - int(self._total_allocated.get("workers", 0)))
        return 0.0

    def estimate_cost(self, task_id: str) -> Dict[str, float]:
        return dict(self._allocated.get(task_id, {}))

    def get_utilization(self) -> Dict[str, float]:
        return {
            "cpu": round(self._total_allocated.get("cpu", 0) / max(1, self._pool.cpu_cores), 3),
            "memory": round(self._total_allocated.get("memory", 0) / max(1, self._pool.memory_gb), 3),
            "workers": round(self._total_allocated.get("workers", 0) / max(1, self._pool.worker_slots), 3),
        }

    def _can_allocate(self, resources: Dict[str, float]) -> bool:
        for key, amount in resources.items():
            if self.available(key) < amount:
                return False
        return True

    def get_stats(self) -> Dict[str, Any]:
        return {
            "pool": self._pool.to_dict(),
            "allocated": self._total_allocated,
            "utilization": self.get_utilization(),
            "active_tasks": len(self._allocated),
        }
