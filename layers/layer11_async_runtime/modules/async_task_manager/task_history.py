"""Bounded thread-safe task execution history."""
from __future__ import annotations

import threading
import time
from typing import Any, Dict, List


class TaskHistory:
    def __init__(self, max_entries: int = 1_000) -> None:
        if isinstance(max_entries, bool) or not isinstance(max_entries, int) or max_entries < 1:
            raise ValueError("max_entries must be a positive integer")
        self._max = max_entries
        self._entries: List[Dict[str, Any]] = []
        self._lock = threading.RLock()

    def record(self, task_id: str, state: str, result: Any = None) -> None:
        if not task_id or not state:
            raise ValueError("task_id and state must be non-empty")
        with self._lock:
            self._entries.append({
                "task_id": task_id,
                "state": state,
                "time": time.time(),
            })
            if len(self._entries) > self._max:
                del self._entries[:-self._max]

    def get_recent(self, count: int = 20) -> List[Dict[str, Any]]:
        if isinstance(count, bool) or not isinstance(count, int) or count < 0:
            raise ValueError("count must be a non-negative integer")
        with self._lock:
            return list(self._entries[-count:]) if count else []

    def get_stats(self) -> Dict[str, int]:
        with self._lock:
            return {"total": len(self._entries)}
