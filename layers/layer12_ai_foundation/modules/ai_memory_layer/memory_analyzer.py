"""MemoryAnalyzer — analyze memory system health and quality."""
from __future__ import annotations

import time
from typing import Any, Dict, List

from .models import MemoryEntry


class MemoryAnalyzer:
    """Analyze memory system health, quality, and patterns."""

    def __init__(self) -> None:
        self._analysis_cache: Dict[str, Dict[str, Any]] = {}

    def analyze(self, entries: List[MemoryEntry]) -> Dict[str, Any]:
        if not entries:
            return {"total": 0, "avg_importance": 0.0, "by_type": {}}

        type_counts: Dict[str, int] = {}
        for e in entries:
            t = e.memory_type.value
            type_counts[t] = type_counts.get(t, 0) + 1

        avg_importance = sum(e.importance for e in entries) / len(entries)
        avg_access = sum(e.access_count for e in entries) / len(entries)
        avg_age_days = sum((time.time() - e.created_at) / 86400 for e in entries) / len(entries)

        # Duplicate detection (simple content hash)
        content_hashes: Dict[str, int] = {}
        for e in entries:
            h = hash(e.content.lower().strip()) % 10**8
            content_hashes[h] = content_hashes.get(h, 0) + 1
        duplicates = sum(v - 1 for v in content_hashes.values() if v > 1)

        return {
            "total": len(entries), "avg_importance": round(avg_importance, 4),
            "avg_access_count": round(avg_access, 2), "avg_age_days": round(avg_age_days, 2),
            "by_type": type_counts, "duplicates": duplicates,
            "unique_ratio": 1 - duplicates / max(len(entries), 1),
        }

    def get_slow_access(self, entries: List[MemoryEntry],
                        threshold: int = 0) -> List[MemoryEntry]:
        return [e for e in entries if e.access_count <= threshold]

    def get_stale(self, entries: List[MemoryEntry],
                  max_age_days: float = 30) -> List[MemoryEntry]:
        now = time.time()
        return [e for e in entries if (now - e.last_accessed) / 86400 > max_age_days]
