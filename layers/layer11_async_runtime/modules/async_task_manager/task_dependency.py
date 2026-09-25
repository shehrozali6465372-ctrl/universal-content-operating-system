"""Thread-safe task dependency registry."""
from __future__ import annotations

import threading
from typing import Dict, List, Set


class TaskDependency:
    def __init__(self) -> None:
        self._deps: Dict[str, Set[str]] = {}
        self._lock = threading.RLock()

    def add(self, task_id: str, depends_on: str) -> None:
        if not task_id or not depends_on:
            raise ValueError("task ids must be non-empty")
        if task_id == depends_on:
            raise ValueError("a task cannot depend on itself")
        with self._lock:
            self._deps.setdefault(task_id, set()).add(depends_on)

    def get(self, task_id: str) -> List[str]:
        with self._lock:
            return sorted(self._deps.get(task_id, set()))

    def is_satisfied(self, task_id: str, completed: Set[str]) -> bool:
        if not isinstance(completed, set):
            raise TypeError("completed must be a set")
        with self._lock:
            return self._deps.get(task_id, set()).issubset(completed)

    def get_stats(self) -> Dict[str, int]:
        with self._lock:
            return {"total_dependencies": sum(len(values) for values in self._deps.values())}
