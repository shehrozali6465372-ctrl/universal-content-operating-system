"""Worker Pool — Manage execution workers."""
from __future__ import annotations
import itertools
import time
from typing import Any, Dict, List, Optional

_WP_COUNTER = itertools.count(1)


class Worker:
    """An execution worker."""

    __slots__ = ("worker_id", "status", "current_task", "tasks_completed",
                 "tasks_failed", "cpu_usage", "memory_usage", "last_heartbeat",
                 "total_runtime_ms")

    def __init__(self, worker_id: str = "") -> None:
        self.worker_id = worker_id or f"worker_{next(_WP_COUNTER)}"
        self.status: str = "idle"
        self.current_task: Optional[str] = None
        self.tasks_completed: int = 0
        self.tasks_failed: int = 0
        self.cpu_usage: float = 0.0
        self.memory_usage: float = 0.0
        self.last_heartbeat: float = time.time()
        self.total_runtime_ms: float = 0.0

    @property
    def is_busy(self) -> bool:
        return self.status == "busy"

    @property
    def is_available(self) -> bool:
        return self.status == "idle"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "worker_id": self.worker_id,
            "status": self.status,
            "current_task": self.current_task,
            "tasks_completed": self.tasks_completed,
            "tasks_failed": self.tasks_failed,
        }


class WorkerPool:
    """Manage a pool of execution workers."""

    def __init__(self, size: int = 10) -> None:
        self._workers: List[Worker] = []
        for i in range(size):
            self._workers.append(Worker(f"worker_{i+1}"))

    def assign(self, task_id: str) -> Optional[Worker]:
        for worker in self._workers:
            if worker.is_available:
                worker.status = "busy"
                worker.current_task = task_id
                return worker
        return None

    def release(self, worker_id: str, success: bool = True) -> bool:
        for worker in self._workers:
            if worker.worker_id == worker_id:
                if success:
                    worker.tasks_completed += 1
                else:
                    worker.tasks_failed += 1
                worker.status = "idle"
                worker.current_task = None
                return True
        return False

    def heartbeat(self, worker_id: str, cpu: float = 0.0, memory: float = 0.0) -> bool:
        for worker in self._workers:
            if worker.worker_id == worker_id:
                worker.last_heartbeat = time.time()
                worker.cpu_usage = cpu
                worker.memory_usage = memory
                return True
        return False

    def get_worker(self, worker_id: str) -> Optional[Worker]:
        for w in self._workers:
            if w.worker_id == worker_id:
                return w
        return None

    def get_idle_workers(self) -> List[Worker]:
        return [w for w in self._workers if w.is_available]

    def get_busy_workers(self) -> List[Worker]:
        return [w for w in self._workers if w.is_busy]

    @property
    def idle_count(self) -> int:
        return len(self.get_idle_workers())

    @property
    def busy_count(self) -> int:
        return len(self.get_busy_workers())

    @property
    def pool_size(self) -> int:
        return len(self._workers)

    def get_stats(self) -> Dict[str, Any]:
        return {
            "pool_size": self.pool_size,
            "idle": self.idle_count,
            "busy": self.busy_count,
            "total_completed": sum(w.tasks_completed for w in self._workers),
            "total_failed": sum(w.tasks_failed for w in self._workers),
        }
