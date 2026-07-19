"""GovernanceMemory — remember governance decisions."""
from __future__ import annotations
import time
from typing import Any, Dict, List

class GovernanceMemory:
    def __init__(self, max_entries: int = 500) -> None:
        self.max_entries = max_entries; self._entries: List[Dict[str, Any]] = []
    def store(self, content_hash: str, decision: str, details: Dict[str, Any] | None = None) -> None:
        self._entries.append({"hash": content_hash, "decision": decision,
                              "details": details or {}, "timestamp": time.time()})
        if len(self._entries) > self.max_entries: self._entries = self._entries[-self.max_entries:]
    def recall(self, content_hash: str) -> Dict[str, Any] | None:
        for e in reversed(self._entries):
            if e["hash"] == content_hash: return e
        return None
    def count(self) -> int: return len(self._entries)
    def clear(self) -> None: self._entries.clear()
