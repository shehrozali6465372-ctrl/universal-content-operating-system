"""TaskCancel — Cancellation support."""
from __future__ import annotations
class TaskCancel:
    def __init__(self): self._cancelled = set()
    def cancel(self, task_id: str): self._cancelled.add(task_id)
    def is_cancelled(self, task_id: str) -> bool: return task_id in self._cancelled
    def clear(self): self._cancelled.clear()
