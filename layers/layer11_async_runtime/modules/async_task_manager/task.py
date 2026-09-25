"""Thread-safe task lifecycle wrapper with explicit state transitions."""
from __future__ import annotations

import threading
import time
from typing import Any, Dict

from layers.layer11_async_runtime.modules.async_task_manager.models import AsyncTask, TaskState


class Task:
    """Own one canonical AsyncTask and serialize lifecycle transitions."""

    def __init__(self, name: str = "", priority: int = 1) -> None:
        self._task = AsyncTask(name, priority)
        self._lock = threading.RLock()

    @property
    def id(self) -> str:
        return self._task.task_id

    @property
    def state(self) -> TaskState:
        with self._lock:
            return self._task.state

    def start(self) -> None:
        with self._lock:
            if self._task.state != TaskState.PENDING:
                raise RuntimeError("task is not pending")
            self._task.state = TaskState.RUNNING
            self._task.started_at = time.time()

    def complete(self, result: Any = None) -> None:
        with self._lock:
            if self._task.state != TaskState.RUNNING:
                raise RuntimeError("task is not running")
            self._task.state = TaskState.COMPLETED
            self._task.result = result
            self._task.completed_at = time.time()

    def fail(self, error: str = "") -> None:
        if not isinstance(error, str):
            error = str(error)
        with self._lock:
            if self._task.state != TaskState.RUNNING:
                raise RuntimeError("task is not running")
            self._task.state = TaskState.FAILED
            self._task.error = error
            self._task.completed_at = time.time()

    def cancel(self) -> None:
        with self._lock:
            if self._task.state not in (TaskState.PENDING, TaskState.RUNNING):
                raise RuntimeError("task cannot be cancelled")
            self._task.state = TaskState.CANCELLED
            self._task.completed_at = time.time()

    def to_dict(self) -> Dict[str, Any]:
        with self._lock:
            return self._task.to_dict()
