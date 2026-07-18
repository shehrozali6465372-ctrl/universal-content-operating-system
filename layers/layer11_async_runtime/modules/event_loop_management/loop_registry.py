"""LoopRegistry — Track all event loops."""
from __future__ import annotations
import time
from typing import Any, Dict, List

class LoopEntry:
    __slots__ = ("loop_id", "status", "registered_at")
    def __init__(self, loop_id: str = "") -> None:
        self.loop_id = loop_id
        self.status: str = "active"
        self.registered_at: float = time.time()

class LoopRegistry:
    def __init__(self) -> None:
        self._entries: Dict[str, LoopEntry] = {}
    def register(self, loop_id: str) -> LoopEntry:
        if loop_id not in self._entries:
            self._entries[loop_id] = LoopEntry(loop_id)
        return self._entries[loop_id]
    def unregister(self, loop_id: str) -> bool:
        return self._entries.pop(loop_id, None) is not None
    def get_all(self) -> List[LoopEntry]:
        return list(self._entries.values())
    def get_stats(self) -> Dict[str, Any]:
        return {"total": len(self._entries)}
