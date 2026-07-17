"""Brand Memory — Store and retrieve brand voice learnings."""
from __future__ import annotations
import time
import itertools
from typing import Any, Dict, List, Optional

_BM_COUNTER = itertools.count(1)


class BrandMemoryEntry:
    """A stored brand voice learning entry."""

    __slots__ = ("entry_id", "brand_id", "learning_type", "description",
                 "confidence", "created_at", "tags", "archived")

    def __init__(self, brand_id: str = "", learning_type: str = "insight") -> None:
        self.entry_id: str = f"bme_{next(_BM_COUNTER)}"
        self.brand_id = brand_id
        self.learning_type = learning_type
        self.description: str = ""
        self.confidence: float = 0.5
        self.created_at: float = time.time()
        self.tags: List[str] = []
        self.archived: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "brand_id": self.brand_id,
            "learning_type": self.learning_type,
            "description": self.description,
            "confidence": round(self.confidence, 3),
            "tags": self.tags,
        }


class BrandMemory:
    """Store and retrieve brand voice learnings."""

    def __init__(self, max_entries: int = 5000) -> None:
        self._max_entries = max_entries
        self._entries: List[BrandMemoryEntry] = []

    def store(self, brand_id: str, learning_type: str, description: str,
              confidence: float = 0.5, tags: Optional[List[str]] = None) -> BrandMemoryEntry:
        entry = BrandMemoryEntry(brand_id, learning_type)
        entry.description = description
        entry.confidence = confidence
        if tags:
            entry.tags = list(tags)
        self._entries.append(entry)
        if len(self._entries) > self._max_entries:
            self._entries = self._entries[-self._max_entries:]
        return entry

    def search(self, brand_id: str = "", learning_type: str = "",
               tag: str = "", limit: int = 50) -> List[BrandMemoryEntry]:
        results = [e for e in self._entries if not e.archived]
        if brand_id:
            results = [e for e in results if e.brand_id == brand_id]
        if learning_type:
            results = [e for e in results if e.learning_type == learning_type]
        if tag:
            results = [e for e in results if tag in e.tags]
        return results[-limit:]

    def get_recent(self, count: int = 10) -> List[BrandMemoryEntry]:
        return [e for e in self._entries if not e.archived][-count:]

    def archive(self, entry_id: str) -> bool:
        for e in self._entries:
            if e.entry_id == entry_id:
                e.archived = True
                return True
        return False

    def get_by_id(self, entry_id: str) -> Optional[BrandMemoryEntry]:
        for e in self._entries:
            if e.entry_id == entry_id:
                return e
        return None

    def get_stats(self) -> Dict[str, Any]:
        active = [e for e in self._entries if not e.archived]
        by_type: Dict[str, int] = {}
        for e in active:
            by_type[e.learning_type] = by_type.get(e.learning_type, 0) + 1
        return {
            "total": len(self._entries),
            "active": len(active),
            "archived": len(self._entries) - len(active),
            "by_type": by_type,
        }

    @property
    def entry_count(self) -> int:
        return len([e for e in self._entries if not e.archived])
