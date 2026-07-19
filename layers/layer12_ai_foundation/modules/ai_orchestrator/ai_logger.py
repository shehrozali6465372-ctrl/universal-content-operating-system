"""AILogger — log orchestrator operations."""
from __future__ import annotations
import time
from typing import Any, Dict, List

class AILogger:
    def __init__(self) -> None:
        self._logs: List[Dict[str, Any]] = []
    def log(self, level: str, message: str, data: Dict[str, Any] | None = None) -> None:
        self._logs.append({"level": level, "message": message, "data": data or {}, "time": time.time()})
    def get_logs(self, level: str | None = None) -> List[Dict[str, Any]]:
        if level: return [l for l in self._logs if l["level"] == level]
        return list(self._logs)
    def count(self) -> int: return len(self._logs)
    def clear(self) -> None: self._logs.clear()
