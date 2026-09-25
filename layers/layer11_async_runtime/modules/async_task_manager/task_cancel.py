"""Thread-safe task cancellation registry."""
from __future__ import annotations

import threading
from typing import Set


class TaskCancel:
    def __init__(self) -> None:
        self._cancelled: Set[str] = set()
        self._lock = threading.RLock()

    def cancel(self, task_id: str) -> None:
        if not task_id:
            raise ValueError("task_id must be non-empty")
        with self._lock:
            self._cancelled.add(task_id)

    def is_cancelled(self, task_id: str) -> bool:
        with self._lock:
            return task_id in self._cancelled

    def clear(self) -> None:
        with self._lock:
            self._cancelled.clear()
