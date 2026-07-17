"""Prompt History — Track version history and performance over time."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional

from layers.layer09_learning.modules.prompt_optimization.prompt_profile import PromptProfile


class HistoryEntry:
    """A single snapshot in prompt history."""

    __slots__ = ("entry_id", "profile_id", "version", "action",
                 "timestamp", "metrics", "notes")

    _counter = 0

    def __init__(self, profile_id: str = "", version: int = 0, action: str = "created") -> None:
        PromptHistory._entry_counter += 1
        self.entry_id: str = f"phe_{PromptHistory._entry_counter}"
        self.profile_id = profile_id
        self.version = version
        self.action = action
        self.timestamp: float = time.time()
        self.metrics: Dict[str, float] = {}
        self.notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "profile_id": self.profile_id,
            "version": self.version,
            "action": self.action,
            "timestamp": self.timestamp,
            "metrics": self.metrics,
        }


class PromptHistory:
    """Track all changes and performance snapshots for prompts."""

    _entry_counter = 0

    def __init__(self, max_entries: int = 10000) -> None:
        self._max_entries = max_entries
        self._entries: List[HistoryEntry] = []

    def record(self, profile: PromptProfile, action: str = "created",
               metrics: Optional[Dict[str, float]] = None, notes: str = "") -> HistoryEntry:
        entry = HistoryEntry(profile.profile_id, profile.version, action)
        if metrics:
            entry.metrics = dict(metrics)
        entry.notes = notes
        self._entries.append(entry)
        if len(self._entries) > self._max_entries:
            self._entries = self._entries[-self._max_entries:]
        return entry

    def get_profile_history(self, profile_id: str) -> List[HistoryEntry]:
        return [e for e in self._entries if e.profile_id == profile_id]

    def get_version_history(self, profile_id: str) -> List[HistoryEntry]:
        entries = self.get_profile_history(profile_id)
        return sorted(entries, key=lambda e: e.version)

    def get_recent(self, count: int = 10) -> List[HistoryEntry]:
        return list(self._entries[-count:])

    def get_by_action(self, action: str) -> List[HistoryEntry]:
        return [e for e in self._entries if e.action == action]

    def get_performance_snapshots(self, profile_id: str) -> List[Dict[str, float]]:
        snapshots = []
        for e in self.get_profile_history(profile_id):
            if e.metrics:
                snapshots.append({"version": e.version, **e.metrics})
        return snapshots

    def get_best_version(self, profile_id: str, metric: str = "engagement") -> Optional[int]:
        best_version = None
        best_value = -1.0
        for e in self.get_profile_history(profile_id):
            val = e.metrics.get(metric, 0.0)
            if val > best_value:
                best_value = val
                best_version = e.version
        return best_version

    @property
    def entry_count(self) -> int:
        return len(self._entries)
