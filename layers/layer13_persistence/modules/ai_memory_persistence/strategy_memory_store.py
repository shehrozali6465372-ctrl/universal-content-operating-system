"""strategy_memory_store.py — Strategy memory persistence."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from layers.layer13_persistence.modules.ai_memory_persistence.base_memory_store import BaseMemoryStore, MemoryEntry


class StrategyMemoryStore(BaseMemoryStore):
    """Stores strategies and their outcomes."""

    def __init__(self, max_entries: int = 5000) -> None:
        super().__init__("strategy", max_entries)
        self._outcomes: Dict[str, List[Dict[str, Any]]] = {}

    def store(self, key: str, value: Any, metadata: Dict[str, Any] = None) -> MemoryEntry:
        entry = MemoryEntry(key, value, "strategy")
        if metadata:
            entry.metadata = metadata
        self._store[key] = entry
        return entry

    def retrieve(self, key: str) -> Optional[MemoryEntry]:
        entry = self._store.get(key)
        if entry:
            entry.access_count += 1
        return entry

    def record_outcome(self, strategy_key: str, outcome: Dict[str, Any]) -> None:
        if strategy_key not in self._outcomes:
            self._outcomes[strategy_key] = []
        self._outcomes[strategy_key].append(outcome)

    def get_outcomes(self, strategy_key: str) -> List[Dict[str, Any]]:
        return list(self._outcomes.get(strategy_key, []))

    def get_best_strategy(self) -> Optional[str]:
        best_key, best_score = None, -1
        for key, outcomes in self._outcomes.items():
            avg = sum(o.get("score", 0) for o in outcomes) / max(1, len(outcomes))
            if avg > best_score:
                best_score = avg
                best_key = key
        return best_key

    def stats(self) -> Dict[str, Any]:
        base = super().stats()
        base["strategies_with_outcomes"] = len(self._outcomes)
        return base
