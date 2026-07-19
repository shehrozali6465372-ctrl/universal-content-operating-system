"""EvalMemory — remember evaluation history."""
from __future__ import annotations
import time
from typing import Any, Dict, List

class EvalMemory:
    def __init__(self, max_entries: int = 500) -> None:
        self.max_entries = max_entries; self._entries: List[Dict[str, Any]] = []
    def store(self, content_hash: str, eval_type: str, score: float, passed: bool) -> None:
        self._entries.append({"hash": content_hash, "type": eval_type, "score": score,
                              "passed": passed, "timestamp": time.time()})
        if len(self._entries) > self.max_entries: self._entries = self._entries[-self.max_entries:]
    def get_by_type(self, eval_type: str, limit: int = 10) -> List[Dict[str, Any]]:
        return [e for e in self._entries if e["type"] == eval_type][-limit:]
    def success_rate(self) -> float:
        if not self._entries: return 0.0
        return sum(1 for e in self._entries if e["passed"]) / len(self._entries)
    def count(self) -> int: return len(self._entries)
    def clear(self) -> None: self._entries.clear()
