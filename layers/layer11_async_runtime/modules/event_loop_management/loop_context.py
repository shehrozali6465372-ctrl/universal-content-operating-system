"""LoopContext — Context for loop operations."""
from __future__ import annotations
import time
from typing import Any, Dict

class LoopContext:
    def __init__(self, loop_id: str = "") -> None:
        self.loop_id = loop_id
        self.data: Dict[str, Any] = {}
        self.created_at: float = time.time()
    def set(self, key: str, value: Any) -> None:
        self.data[key] = value
    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)
    def to_dict(self) -> Dict[str, Any]:
        return {"loop_id": self.loop_id, "data": self.data}
