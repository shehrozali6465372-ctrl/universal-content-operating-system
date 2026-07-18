"""MemorySearch — unified search across all memory types."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .models import MemoryEntry, MemoryType


class MemorySearch:
    """Unified search engine across all memory types."""

    def __init__(self) -> None:
        self._search_history: List[Dict[str, Any]] = []

    def search(self, stores: Dict[str, List[MemoryEntry]],
               query: str, memory_type: Optional[MemoryType] = None,
               tags: Optional[List[str]] = None, limit: int = 10) -> List[MemoryEntry]:
        query_words = set(query.lower().split())
        candidates: List[tuple] = []

        target_stores = [memory_type.value] if memory_type else list(stores.keys())
        for store_type in target_stores:
            for entry in stores.get(store_type, []):
                content_words = set(entry.content.lower().split())
                score = len(query_words & content_words) / max(len(query_words), 1) if query_words else 0.5
                if tags and not any(t in entry.tags for t in tags):
                    continue
                score += entry.importance * 0.2
                if score > 0:
                    candidates.append((entry, score))

        candidates.sort(key=lambda x: x[1], reverse=True)
        results = [e for e, _ in candidates[:limit]]

        self._search_history.append({"query": query[:100], "results": len(results)})
        return results

    def get_history(self) -> List[Dict[str, Any]]:
        return list(self._search_history)
