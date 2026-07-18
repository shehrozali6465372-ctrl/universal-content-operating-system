"""TaskScheduler — Schedule tasks with priorities."""
from __future__ import annotations
import heapq
from typing import Any, Dict, List, Optional
from layers.layer11_async_runtime.modules.async_task_manager.models import AsyncTask

class TaskScheduler:
    def __init__(self): self._queue: List[tuple] = []; self._tasks: Dict[str, AsyncTask] = {}
    def schedule(self, task: AsyncTask) -> None:
        self._tasks[task.task_id] = task
        heapq.heappush(self._queue, (task.priority, task.task_id))
    def next(self) -> Optional[AsyncTask]:
        while self._queue:
            _, tid = heapq.heappop(self._queue)
            if tid in self._tasks and self._tasks[tid].state == "pending":
                return self._tasks[tid]
        return None
    def size(self) -> int: return len(self._queue)
    def get_stats(self) -> Dict[str, Any]: return {"queued": len(self._queue), "total": len(self._tasks)}
