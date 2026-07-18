"""MemoryLifecycle — manage memory lifecycle from creation to archival."""
from __future__ import annotations

import time
from typing import Any, Dict, List

from .models import MemoryEntry


class MemoryLifecycle:
    """Manage memory lifecycle: create → active → dormant → archive → delete."""

    STAGES = ("active", "dormant", "archived", "deleted")

    def __init__(self, dormant_threshold_days: float = 7.0,
                 archive_threshold_days: float = 30.0) -> None:
        self.dormant_threshold_days = dormant_threshold_days
        self.archive_threshold_days = archive_threshold_days
        self._transitions: List[Dict[str, Any]] = []

    def get_stage(self, entry: MemoryEntry) -> str:
        age_days = (time.time() - entry.last_accessed) / 86400
        if entry.importance > 0.7 and age_days < self.dormant_threshold_days:
            return "active"
        elif age_days < self.archive_threshold_days:
            return "dormant"
        elif entry.importance > 0.3:
            return "archived"
        return "deleted"

    def apply_lifecycle(self, entries: List[MemoryEntry]) -> Dict[str, List[MemoryEntry]]:
        result: Dict[str, List[MemoryEntry]] = {s: [] for s in self.STAGES}
        for e in entries:
            stage = self.get_stage(e)
            result[stage].append(e)
        return result

    def get_transition_count(self) -> int:
        return len(self._transitions)

    def to_dict(self) -> Dict[str, Any]:
        return {"dormant_days": self.dormant_threshold_days,
                "archive_days": self.archive_threshold_days}
