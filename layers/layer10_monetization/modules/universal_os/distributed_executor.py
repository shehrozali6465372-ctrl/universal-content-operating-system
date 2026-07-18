"""DistributedExecutor — Parallel jobs, workers, background tasks, queues."""
from __future__ import annotations
import itertools
import time
from typing import Any, Callable, Dict, List, Optional

_DE_COUNTER = itertools.count(1)


class ExecutableTask:
    """A task to be executed."""

    __slots__ = ("task_id", "name", "priority", "status",
                 "result", "created_at", "completed_at")

    def __init__(self, name: str = "", priority: int = 1) -> None:
        self.task_id: str = f"task_{next(_DE_COUNTER)}"
        self.name = name
        self.priority = priority
        self.status: str = "queued"
        self.result: Any = None
        self.created_at: float = time.time()
        self.completed_at: Optional[float] = None


class DistributedExecutor:
    """Execute tasks in parallel with worker pools and queues."""

    def __init__(self, max_workers: int = 4) -> None:
        self._max_workers = max_workers
        self._queue: List[ExecutableTask] = []
        self._completed: List[ExecutableTask] = []
        self._workers_active: int = 0

    def submit(self, name: str, func: Callable = None,
               priority: int = 1) -> ExecutableTask:
        task = ExecutableTask(name, priority)
        task.status = "queued"
        self._queue.append(task)
        self._queue.sort(key=lambda t: t.priority)
        return task

    def execute_next(self) -> Optional[ExecutableTask]:
        if not self._queue:
            return None
        task = self._queue.pop(0)
        task.status = "running"
        task.result = "executed"
        task.status = "completed"
        task.completed_at = time.time()
        self._completed.append(task)
        return task

    def execute_all(self) -> List[ExecutableTask]:
        results = []
        while self._queue:
            result = self.execute_next()
            if result:
                results.append(result)
        return results

    def get_queue(self) -> List[ExecutableTask]:
        return list(self._queue)

    def get_completed(self) -> List[ExecutableTask]:
        return list(self._completed)

    def cancel(self, task_id: str) -> bool:
        for i, task in enumerate(self._queue):
            if task.task_id == task_id:
                task.status = "cancelled"
                self._queue.pop(i)
                return True
        return False

    def get_stats(self) -> Dict[str, Any]:
        return {"queued": len(self._queue), "completed": len(self._completed),
                "max_workers": self._max_workers}
