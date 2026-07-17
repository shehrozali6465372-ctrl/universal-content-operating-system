"""Strategy History — Track strategy version history and performance over time."""
from __future__ import annotations
import time
import itertools
from typing import Any, Dict, List, Optional

from layers.layer09_learning.modules.strategy_optimization.strategy_profile import StrategyProfile

_SH_COUNTER = itertools.count(1)


class StrategyHistoryEntry:
    """A single snapshot in strategy history."""

    __slots__ = ("entry_id", "strategy_id", "version", "action",
                 "timestamp", "metrics", "notes")

    def __init__(self, strategy_id: str = "", version: int = 0, action: str = "created") -> None:
        self.entry_id: str = f"she_{next(_SH_COUNTER)}"
        self.strategy_id = strategy_id
        self.version = version
        self.action = action
        self.timestamp: float = time.time()
        self.metrics: Dict[str, float] = {}
        self.notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "strategy_id": self.strategy_id,
            "version": self.version,
            "action": self.action,
            "timestamp": self.timestamp,
            "metrics": self.metrics,
        }


class StrategyHistory:
    """Track all changes and performance snapshots for strategies."""

    def __init__(self, max_entries: int = 10000) -> None:
        self._max_entries = max_entries
        self._entries: List[StrategyHistoryEntry] = []

    def record(self, strategy: StrategyProfile, action: str = "created",
               metrics: Optional[Dict[str, float]] = None, notes: str = "") -> StrategyHistoryEntry:
        entry = StrategyHistoryEntry(strategy.strategy_id, strategy.version, action)
        if metrics:
            entry.metrics = dict(metrics)
        entry.notes = notes
        self._entries.append(entry)
        if len(self._entries) > self._max_entries:
            self._entries = self._entries[-self._max_entries:]
        return entry

    def get_strategy_history(self, strategy_id: str) -> List[StrategyHistoryEntry]:
        return [e for e in self._entries if e.strategy_id == strategy_id]

    def get_recent(self, count: int = 10) -> List[StrategyHistoryEntry]:
        return list(self._entries[-count:])

    def get_by_action(self, action: str) -> List[StrategyHistoryEntry]:
        return [e for e in self._entries if e.action == action]

    def get_performance_snapshots(self, strategy_id: str) -> List[Dict[str, float]]:
        snapshots = []
        for e in self.get_strategy_history(strategy_id):
            if e.metrics:
                snapshots.append({"version": e.version, **e.metrics})
        return snapshots

    def get_best_version(self, strategy_id: str, metric: str = "engagement") -> Optional[int]:
        best_version = None
        best_value = -1.0
        for e in self.get_strategy_history(strategy_id):
            val = e.metrics.get(metric, 0.0)
            if val > best_value:
                best_value = val
                best_version = e.version
        return best_version

    @property
    def entry_count(self) -> int:
        return len(self._entries)
