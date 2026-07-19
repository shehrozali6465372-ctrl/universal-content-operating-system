"""ReasoningMemory — remember past reasoning chains and outcomes."""
from __future__ import annotations

import time
from typing import Any, Dict, List

from .models import ReasoningChain


class ReasoningMemory:
    """Memory for past reasoning chains and their outcomes."""

    def __init__(self, max_entries: int = 500) -> None:
        self.max_entries = max_entries
        self._entries: List[Dict[str, Any]] = []

    def store(self, chain: ReasoningChain, outcome: str = "",
              success: bool = True) -> None:
        self._entries.append({
            "chain_id": chain.chain_id, "type": chain.reasoning_type.value,
            "conclusion": chain.conclusion, "confidence": chain.confidence,
            "outcome": outcome, "success": success,
            "timestamp": time.time(),
        })
        if len(self._entries) > self.max_entries:
            self._entries = self._entries[-self.max_entries:]

    def recall_by_type(self, reasoning_type: str, limit: int = 5) -> List[Dict[str, Any]]:
        filtered = [e for e in self._entries if e["type"] == reasoning_type]
        return filtered[-limit:]

    def recall_successful(self, limit: int = 5) -> List[Dict[str, Any]]:
        successful = [e for e in self._entries if e["success"]]
        return successful[-limit:]

    def recall_recent(self, limit: int = 5) -> List[Dict[str, Any]]:
        return self._entries[-limit:]

    @property
    def success_rate(self) -> float:
        if not self._entries:
            return 0.0
        return sum(1 for e in self._entries if e["success"]) / len(self._entries)

    def count(self) -> int:
        return len(self._entries)

    def clear(self) -> None:
        self._entries.clear()
