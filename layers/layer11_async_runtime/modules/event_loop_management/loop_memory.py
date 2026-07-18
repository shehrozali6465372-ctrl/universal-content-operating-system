"""LoopMemory — Store loop state for recovery."""
from __future__ import annotations
import time
from typing import Any, Dict, List

class LoopMemory:
    def __init__(self, max_entries: int = 100) -> None:
        self._max = max_entries
        self._entries: List[Dict[str, Any]] = []
    def store(self, loop_id: str, state: Dict[str, Any]) -> None:
        self._entries.append({"loop_id": loop_id, "state": state, "time": time.time()})
        if len(self._entries) > self._max:
            self._entries = self._entries[-self._max:]
    def get_latest(self, loop_id: str = "") -> Dict[str, Any]:
        entries = self._entries
        if loop_id:
            entries = [e for e in entries if e["loop_id"] == loop_id]
        return entries[-1] if entries else {}
    def get_stats(self) -> Dict[str, Any]:
        return {"total": len(self._entries), "max": self._max}
