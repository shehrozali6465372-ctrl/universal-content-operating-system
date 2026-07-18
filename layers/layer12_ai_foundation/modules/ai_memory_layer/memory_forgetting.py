"""MemoryForgetting — manage memory decay, pruning, and forgetting."""
from __future__ import annotations

import time
from typing import List

from .models import MemoryEntry


class MemoryForgetting:
    """Manage memory decay, forgetting curves, and pruning."""

    def __init__(self, default_half_life_days: float = 30.0) -> None:
        self.default_half_life_days = default_half_life_days

    def ebbinghaus_retention(self, age_days: float, half_life_days: float = 30.0) -> float:
        """Ebbinghaus forgetting curve: retention = 2^(-t/h)."""
        if age_days < 0:
            return 1.0
        return 2.0 ** (-age_days / half_life_days)

    def should_forget(self, entry: MemoryEntry, threshold: float = 0.1) -> bool:
        if entry.importance > threshold:
            return False
        age_days = (time.time() - entry.created_at) / 86400
        half_life = self.default_half_life_days * entry.importance * 5
        retention = self.ebbinghaus_retention(age_days, half_life)
        return retention < threshold

    def prune(self, entries: List[MemoryEntry], max_entries: int = 1000) -> List[MemoryEntry]:
        if len(entries) <= max_entries:
            return entries
        scored = [(e, self._forgetting_score(e)) for e in entries]
        scored.sort(key=lambda x: x[1])
        kept = [s[0] for s in scored[-max_entries:]]
        return kept

    def get_forgetting_prone(self, entries: List[MemoryEntry],
                              threshold: float = 0.1) -> List[MemoryEntry]:
        return [e for e in entries if self.should_forget(e, threshold)]

    @staticmethod
    def _forgetting_score(entry: MemoryEntry) -> float:
        age_days = (time.time() - entry.created_at) / 86400
        access_factor = 1.0 / max(entry.access_count, 1)
        return entry.importance - age_days * 0.001 - access_factor * 0.1
