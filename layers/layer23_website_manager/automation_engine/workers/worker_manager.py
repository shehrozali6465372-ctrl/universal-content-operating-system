"""WorkerManager — Manage background worker threads."""
from __future__ import annotations
import time
import threading
from typing import Any, Callable, Dict, List, Optional

from layers.layer23_website_manager.automation_engine.models.automation_models import Worker


class WorkerManager:
    """Manage background workers for automation."""

    def __init__(self, min_workers: int = 2, max_workers: int = 10) -> None:
        self._min_workers: int = min_workers
        self._max_workers: int = max_workers
        self._workers: Dict[str, Worker] = {}
        self._lock = threading.RLock()
        self._task_queue: List[Dict[str, Any]] = []
        self._total_dispatched: int = 0

    def initialize(self) -> None:
        for _ in range(self._min_workers):
            self.add_worker()

    def add_worker(self, name: str = "") -> Worker:
        worker = Worker(name=name)
        with self._lock:
            self._workers[worker.worker_id] = worker
        return worker

    def remove_worker(self, worker_id: str) -> bool:
        with self._lock:
            return self._workers.pop(worker_id, None) is not None

    def get_worker(self, worker_id: str) -> Optional[Worker]:
        return self._workers.get(worker_id)

    def get_idle_worker(self) -> Optional[Worker]:
        with self._lock:
            for w in self._workers.values():
                if not w.is_busy:
                    return w
        return None

    def dispatch(self, task: Dict[str, Any]) -> bool:
        worker = self.get_idle_worker()
        if not worker:
            return False
        with self._lock:
            worker.is_busy = True
            worker.task = task.get("name", "")
            worker.started_at = time.time()
            self._task_queue.append(task)
            self._total_dispatched += 1
        return True

    def complete_task(self, worker_id: str, success: bool = True) -> bool:
        with self._lock:
            worker = self._workers.get(worker_id)
            if not worker:
                return False
            worker.is_busy = False
            worker.task = None
            if success:
                worker.completed_tasks += 1
            else:
                worker.failed_tasks += 1
        return True

    def scale_to(self, count: int) -> int:
        count = max(self._min_workers, min(count, self._max_workers))
        with self._lock:
            current = len(self._workers)
            if count > current:
                for _ in range(count - current):
                    self.add_worker()
            elif count < current:
                # Remove idle workers only
                to_remove = current - count
                for w in list(self._workers.values()):
                    if to_remove <= 0:
                        break
                    if not w.is_busy:
                        self._workers.pop(w.worker_id, None)
                        to_remove -= 1
            return len(self._workers)

    def get_all_workers(self) -> List[Worker]:
        return list(self._workers.values())

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            workers = self._workers.values()
            return {
                "total_workers": len(workers),
                "busy": sum(1 for w in workers if w.is_busy),
                "idle": sum(1 for w in workers if not w.is_busy),
                "total_dispatched": self._total_dispatched,
                "total_completed": sum(w.completed_tasks for w in workers),
                "total_failed": sum(w.failed_tasks for w in workers),
                "queue_size": len(self._task_queue),
                "min_workers": self._min_workers,
                "max_workers": self._max_workers,
            }
