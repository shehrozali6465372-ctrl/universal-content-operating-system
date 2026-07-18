"""MemoryConsolidation — consolidate multiple memories into summaries."""
from __future__ import annotations

from typing import Any, Dict, List

from .models import MemoryEntry, MemoryType


class MemoryConsolidation:
    """Consolidate related memories into summaries or higher-level knowledge."""

    def __init__(self) -> None:
        self._consolidations: List[Dict[str, Any]] = []

    def consolidate(self, entries: List[MemoryEntry]) -> MemoryEntry:
        if not entries:
            return MemoryEntry(content="", memory_type=MemoryType.SEMANTIC, importance=0.0)

        # Merge content into a summary
        topics = set()
        key_points = []
        for e in entries:
            key_points.append(e.content[:100])
            for tag in e.tags:
                topics.add(tag)

        summary = " | ".join(key_points[:5])
        avg_importance = sum(e.importance for e in entries) / len(entries)

        consolidated = MemoryEntry(
            content=summary, memory_type=MemoryType.SEMANTIC,
            tags=list(topics), importance=avg_importance,
            metadata={"consolidated_from": len(entries), "source_total": len(entries)},
        )
        self._consolidations.append({"source_ids": [e.entry_id for e in entries],
                                      "result_id": consolidated.entry_id})
        return consolidated

    def get_history(self) -> List[Dict[str, Any]]:
        return list(self._consolidations)

    def clear(self) -> None:
        self._consolidations.clear()
