"""TaskPause — Pause/resume support."""
from __future__ import annotations
class TaskPause:
    def __init__(self): self._paused = set()
    def pause(self, task_id: str): self._paused.add(task_id)
    def resume(self, task_id: str): self._paused.discard(task_id)
    def is_paused(self, task_id: str) -> bool: return task_id in self._paused
