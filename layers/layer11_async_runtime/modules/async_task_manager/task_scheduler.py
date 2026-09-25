"""Thread-safe priority task scheduler with bounded queueing."""
from __future__ import annotations

import heapq
import threading
from typing import Any, Dict, List, Optional, Tuple

from layers.layer11_async_runtime.modules.async_task_manager.models import AsyncTask, TaskState


class TaskScheduler:
    """Schedule pending tasks by priority without unbounded growth."""

    def __init__(self, max_queue_size: int = 10_000) -> None:
        if isinstance(max_queue_size, bool) or not isinstance(max_queue_size, int):
            raise TypeError("max_queue_size must be an integer")
        if max_queue_size < 1:
            raise ValueError("max_queue_size must be >= 1")
        self._max_queue_size = max_queue_size
        self._queue: List[Tuple[int, str]] = []
        self._tasks: Dict[str, AsyncTask] = {}
        self._lock = threading.RLock()

    def schedule(self, task: AsyncTask) -> None:
        if not isinstance(task, AsyncTask):
            raise TypeError("task must be an AsyncTask")
        with self._lock:
            if len(self._queue) >= self._max_queue_size:
                raise OverflowError("task scheduler queue is full")
            if task.task_id in self._tasks:
                raise ValueError(f"task already scheduled: {task.task_id}")
            if task.state != TaskState.PENDING:
                raise ValueError("only pending tasks can be scheduled")
            self._tasks[task.task_id] = task
            heapq.heappush(self._queue, (task.priority, task.task_id))

    def next(self) -> Optional[AsyncTask]:
        with self._lock:
            while self._queue:
                _, task_id = heapq.heappop(self._queue)
                task = self._tasks.get(task_id)
                if task is not None and task.state == TaskState.PENDING:
                    return task
            return None

    def size(self) -> int:
        with self._lock:
            return len(self._queue)

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            return {"queued": len(self._queue), "total": len(self._tasks)}
