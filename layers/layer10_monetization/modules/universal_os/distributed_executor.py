"""DistributedExecutor — bounded task execution with honest callable results."""
from __future__ import annotations

import itertools
import threading
import time
from typing import Any, Callable, Dict, List, Optional

_DE_COUNTER = itertools.count(1)


class ExecutableTask:
    """A task to be executed."""

    __slots__ = (
        "task_id", "name", "priority", "status", "result",
        "error", "func", "created_at", "completed_at",
    )

    def __init__(
        self, name: str, func: Optional[Callable[[], Any]], priority: int
    ) -> None:
        self.task_id = f"task_{next(_DE_COUNTER)}"
        self.name = name
        self.priority = priority
        self.status = "queued"
        self.result: Any = None
        self.error: Optional[str] = None
        self.func = func
        self.created_at = time.time()
        self.completed_at: Optional[float] = None


class DistributedExecutor:
    """Execute queued tasks with bounded history and synchronized state."""

    def __init__(self, max_workers: int = 4, max_history: int = 10000) -> None:
        if max_workers <= 0 or max_history <= 0:
            raise ValueError("max_workers and max_history must be positive")
        self._max_workers = max_workers
        self._max_history = max_history
        self._queue: List[ExecutableTask] = []
        self._completed: List[ExecutableTask] = []
        self._failed: List[ExecutableTask] = []
        self._workers_active = 0
        self._lock = threading.RLock()

    def submit(
        self,
        name: str,
        func: Optional[Callable[[], Any]] = None,
        priority: int = 1,
    ) -> ExecutableTask:
        if not name:
            raise ValueError("name is required")
        if func is not None and not callable(func):
            raise ValueError("func must be callable")
        task = ExecutableTask(name, func, priority)
        with self._lock:
            self._queue.append(task)
            self._queue.sort(key=lambda item: (item.priority, item.created_at))
        return task

    def execute_next(self) -> Optional[ExecutableTask]:
        with self._lock:
            if not self._queue or self._workers_active >= self._max_workers:
                return None
            task = self._queue.pop(0)
            self._workers_active += 1
            task.status = "running"

        try:
            if task.func is None:
                task.status = "failed"
                task.error = "NoExecutableFunction"
                with self._lock:
                    self._failed.append(task)
            else:
                task.result = task.func()
                task.status = "completed"
                with self._lock:
                    self._completed.append(task)
        except Exception as exc:
            task.status = "failed"
            task.error = type(exc).__name__
            with self._lock:
                self._failed.append(task)
        finally:
            task.completed_at = time.time()
            with self._lock:
                self._workers_active -= 1
                if len(self._completed) > self._max_history:
                    del self._completed[:-self._max_history]
                if len(self._failed) > self._max_history:
                    del self._failed[:-self._max_history]
        return task

    def execute_all(self) -> List[ExecutableTask]:
        results: List[ExecutableTask] = []
        while True:
            task = self.execute_next()
            if task is None:
                with self._lock:
                    if not self._queue:
                        return results
                    if self._workers_active >= self._max_workers:
                        return results
            else:
                results.append(task)

    def get_queue(self) -> List[ExecutableTask]:
        with self._lock:
            return list(self._queue)

    def get_completed(self) -> List[ExecutableTask]:
        with self._lock:
            return list(self._completed)

    def get_failed(self) -> List[ExecutableTask]:
        with self._lock:
            return list(self._failed)

    def cancel(self, task_id: str) -> bool:
        with self._lock:
            for index, task in enumerate(self._queue):
                if task.task_id == task_id:
                    task.status = "cancelled"
                    self._queue.pop(index)
                    return True
        return False

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "queued": len(self._queue),
                "completed": len(self._completed),
                "failed": len(self._failed),
                "max_workers": self._max_workers,
                "max_history": self._max_history,
                "workers_active": self._workers_active,
            }
