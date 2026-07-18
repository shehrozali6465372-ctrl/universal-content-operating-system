"""Models for event loop management."""
from __future__ import annotations
import time
from typing import Any, Dict

class LoopInfo:
    __slots__ = ("loop_id", "status", "tasks_count", "created_at", "metrics")
    def __init__(self, loop_id: str = "") -> None:
        self.loop_id = loop_id
        self.status: str = "created"
        self.tasks_count: int = 0
        self.created_at: float = time.time()
        self.metrics: Dict[str, Any] = {}
    def to_dict(self) -> Dict[str, Any]:
        return {"loop_id": self.loop_id, "status": self.status, "tasks": self.tasks_count}
