"""Execution Scheduler — Schedule layer execution."""
from __future__ import annotations
import itertools
import time
from enum import Enum
from typing import Any, Dict, List, Optional

_ES_COUNTER = itertools.count(1)


class ExecutionMode(Enum):
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    PRIORITY = "priority"


class ScheduledTask:
    """A scheduled execution task."""

    __slots__ = ("task_id", "layer", "status", "priority", "result",
                 "error", "scheduled_at", "started_at", "completed_at", "duration_ms")

    def __init__(self, layer: str = "", priority: int = 0) -> None:
        self.task_id: str = f"task_{next(_ES_COUNTER)}"
        self.layer = layer
        self.status: str = "queued"
        self.priority = priority
        self.result: Any = None
        self.error: Optional[str] = None
        self.scheduled_at: float = time.time()
        self.started_at: float = 0.0
        self.completed_at: float = 0.0
        self.duration_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "layer": self.layer,
            "status": self.status,
            "priority": self.priority,
            "duration_ms": round(self.duration_ms, 1),
        }


class ExecutionScheduler:
    """Schedule and manage layer execution tasks."""

    def __init__(self, mode: ExecutionMode = ExecutionMode.SEQUENTIAL) -> None:
        self._mode = mode
        self._queue: List[ScheduledTask] = []
        self._completed: List[ScheduledTask] = []
        self._max_concurrent: int = 3

    def schedule(self, layer: str, priority: int = 0) -> ScheduledTask:
        task = ScheduledTask(layer, priority)
        self._queue.append(task)
        self._queue.sort(key=lambda t: t.priority, reverse=True)
        return task

    def next_task(self) -> Optional[ScheduledTask]:
        for task in self._queue:
            if task.status == "queued":
                return task
        return None

    def start_task(self, task_id: str) -> Optional[ScheduledTask]:
        for task in self._queue:
            if task.task_id == task_id and task.status == "queued":
                task.status = "running"
                task.started_at = time.time()
                return task
        return None

    def complete_task(self, task_id: str, result: Any = None,
                       error: Optional[str] = None) -> Optional[ScheduledTask]:
        for task in self._queue:
            if task.task_id == task_id and task.status == "running":
                task.completed_at = time.time()
                task.duration_ms = (task.completed_at - task.started_at) * 1000
                task.result = result
                task.error = error
                task.status = "completed" if error is None else "failed"
                self._completed.append(task)
                return task
        return None

    def cancel_task(self, task_id: str) -> bool:
        for task in self._queue:
            if task.task_id == task_id and task.status == "queued":
                task.status = "cancelled"
                return True
        return False

    def get_queue(self) -> List[ScheduledTask]:
        return [t for t in self._queue if t.status in ("queued", "running")]

    def get_completed(self) -> List[ScheduledTask]:
        return list(self._completed)

    def get_stats(self) -> Dict[str, Any]:
        total = len(self._completed)
        successful = sum(1 for t in self._completed if t.status == "completed")
        return {
            "queued": sum(1 for t in self._queue if t.status == "queued"),
            "running": sum(1 for t in self._queue if t.status == "running"),
            "completed": successful,
            "failed": total - successful,
            "total": len(self._queue),
        }
