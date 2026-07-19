"""AIRequest — encapsulate AI processing requests."""
from __future__ import annotations
import uuid
import time
from typing import Any, Dict

class AIRequest:
    def __init__(self, task: str, input_data: Dict[str, Any] | None = None) -> None:
        self.request_id = str(uuid.uuid4())[:12]
        self.task = task; self.input_data = input_data or {}
        self.created_at = time.time(); self.status = "pending"
        self.result: Dict[str, Any] = {}
    def complete(self, result: Dict[str, Any]) -> None:
        self.result = result; self.status = "completed"
    def fail(self, error: str) -> None:
        self.result = {"error": error}; self.status = "failed"
    def to_dict(self) -> Dict[str, Any]:
        return {"request_id": self.request_id, "task": self.task,
                "status": self.status, "created_at": self.created_at}
