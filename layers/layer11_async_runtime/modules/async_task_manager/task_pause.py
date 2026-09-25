"""Thread-safe task pause registry."""
from __future__ import annotations

import threading
from typing import Set


class TaskPause:
    def __init__(self) -> None:
        self._paused: Set[str] = set()
        self._lock = threading.RLock()

    def pause(self, task_id: str) -> None:
        if not task_id:
            raise ValueError("task_id must be non-empty")
        with self._lock:
            self._paused.add(task_id)

    def resume(self, task_id: str) -> None:
        if not task_id:
            raise ValueError("task_id must be non-empty")
        with self._lock:
            self._paused.discard(task_id)

    def is_paused(self, task_id: str) -> bool:
        with self._lock:
            return task_id in self._paused
