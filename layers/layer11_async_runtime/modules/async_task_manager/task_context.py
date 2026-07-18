"""TaskContext — Execution context per task."""
from __future__ import annotations
import time
from typing import Any, Dict
class TaskContext:
    def __init__(self, task_id: str=""):
        self.task_id = task_id
        self.data: Dict[str, Any] = {}
        self.created_at: float = time.time()
    def set(self, k: str, v: Any): self.data[k] = v
    def get(self, k: str, d: Any=None): return self.data.get(k, d)
    def to_dict(self): return {"task_id": self.task_id, "data": self.data}
