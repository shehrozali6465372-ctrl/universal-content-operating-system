"""AIMemory — memory for orchestrator decisions and outcomes."""
from __future__ import annotations
import time
from typing import Any, Dict, List

class AIMemory:
    def __init__(self, max_entries: int = 500) -> None:
        self.max_entries = max_entries; self._entries: List[Dict[str, Any]] = []
    def store(self, decision: str, outcome: str, metadata: Dict[str, Any] | None = None) -> None:
        self._entries.append({"decision": decision, "outcome": outcome,
                              "metadata": metadata or {}, "timestamp": time.time()})
        if len(self._entries) > self.max_entries: self._entries = self._entries[-self.max_entries:]
    def recall(self, decision: str) -> List[Dict[str, Any]]:
        return [e for e in self._entries if e["decision"] == decision]
    def recent(self, limit: int = 5) -> List[Dict[str, Any]]:
        return self._entries[-limit:]
    def count(self) -> int: return len(self._entries)
    def clear(self) -> None: self._entries.clear()
