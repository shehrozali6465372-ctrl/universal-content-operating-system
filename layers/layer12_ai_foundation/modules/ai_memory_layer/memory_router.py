"""MemoryRouter — route memory operations to the correct memory store."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .models import MemoryEntry, MemoryType, MemoryQuery


class MemoryRouter:
    """Route memory operations to the correct memory store."""

    def __init__(self) -> None:
        self._stores: Dict[str, List[MemoryEntry]] = {t.value: [] for t in MemoryType}
        self._max_per_type: int = 1000

    def store(self, entry: MemoryEntry) -> bool:
        key = entry.memory_type.value
        if key not in self._stores:
            self._stores[key] = []
        if len(self._stores[key]) >= self._max_per_type:
            # Evict least important
            self._stores[key].sort(key=lambda e: e.importance)
            self._stores[key].pop(0)
        self._stores[key].append(entry)
        return True

    def retrieve(self, entry_id: str) -> Optional[MemoryEntry]:
        for entries in self._stores.values():
            for e in entries:
                if e.entry_id == entry_id:
                    e.touch()
                    return e
        return None

    def search(self, query: MemoryQuery) -> List[MemoryEntry]:
        candidates: List[MemoryEntry] = []
        target_types = [query.memory_type.value] if query.memory_type else list(self._stores.keys())
        for mt in target_types:
            for entry in self._stores.get(mt, []):
                if query.tags and not any(t in entry.tags for t in query.tags):
                    continue
                if entry.importance < query.min_importance:
                    continue
                if entry.is_expired and not query.include_expired:
                    continue
                candidates.append(entry)

        if query.sort_by == "recency":
            candidates.sort(key=lambda e: e.last_accessed, reverse=True)
        elif query.sort_by == "importance":
            candidates.sort(key=lambda e: e.importance, reverse=True)
        else:
            candidates.sort(key=lambda e: e.confidence, reverse=True)

        return candidates[:query.limit]

    def count(self, memory_type: Optional[MemoryType] = None) -> int:
        if memory_type:
            return len(self._stores.get(memory_type.value, []))
        return sum(len(v) for v in self._stores.values())

    def clear(self, memory_type: Optional[MemoryType] = None) -> None:
        if memory_type:
            self._stores[memory_type.value] = []
        else:
            for k in self._stores:
                self._stores[k] = []

    def stats(self) -> Dict[str, Any]:
        return {k: len(v) for k, v in self._stores.items()}
