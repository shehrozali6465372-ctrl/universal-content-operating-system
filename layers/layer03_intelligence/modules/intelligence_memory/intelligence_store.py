"""Intelligence Store — Core storage for intelligence entries."""
from __future__ import annotations
import itertools
import time
from typing import Any, Dict, List, Optional


class IntelligenceEntry:
    """A single intelligence entry."""
    __slots__ = ("entry_id", "category", "data", "confidence", "score",
                 "tags", "source", "version", "created_at", "updated_at",
                 "access_count", "value")

    def __init__(self, category: str = "", data: Optional[Dict] = None) -> None:
        self.entry_id = f"ientry_{next(_ENTRY_COUNTER)}"
        self.category = category
        self.data = data or {}
        self.confidence = 0.5
        self.score = 0.0
        self.tags: List[str] = []
        self.source = ""
        self.version = 1
        self.created_at = time.time()
        self.updated_at = time.time()
        self.access_count = 0
        self.value = 0.5

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "category": self.category,
            "confidence": round(self.confidence, 3),
            "score": round(self.score, 3),
            "tags": self.tags,
            "source": self.source,
            "version": self.version,
            "access_count": self.access_count,
        }


_ENTRY_COUNTER = itertools.count(1)


class IntelligenceStore:
    """Stores and manages intelligence entries."""

    def __init__(self, max_size: int = 1000) -> None:
        self._entries: Dict[str, IntelligenceEntry] = {}
        self._category_index: Dict[str, List[str]] = {}
        self._tag_index: Dict[str, List[str]] = {}
        self._max_size = max_size

    def store(self, category: str, data: Dict[str, Any], confidence: float = 0.5,
              score: float = 0.0, tags: Optional[List[str]] = None,
              source: str = "") -> IntelligenceEntry:
        """Store a new intelligence entry."""
        entry = IntelligenceEntry(category=category, data=data)
        entry.confidence = confidence
        entry.score = score
        entry.tags = tags or []
        entry.source = source

        if len(self._entries) >= self._max_size:
            oldest = min(self._entries.values(), key=lambda e: e.access_count)
            self._remove_entry(oldest.entry_id)

        self._entries[entry.entry_id] = entry
        self._category_index.setdefault(category, []).append(entry.entry_id)
        for tag in entry.tags:
            self._tag_index.setdefault(tag, []).append(entry.entry_id)
        return entry

    def get(self, entry_id: str) -> Optional[IntelligenceEntry]:
        entry = self._entries.get(entry_id)
        if entry:
            entry.access_count += 1
        return entry

    def get_by_category(self, category: str) -> List[IntelligenceEntry]:
        ids = self._category_index.get(category, [])
        return [self._entries[i] for i in ids if i in self._entries]

    def get_by_tag(self, tag: str) -> List[IntelligenceEntry]:
        ids = self._tag_index.get(tag, [])
        return [self._entries[i] for i in ids if i in self._entries]

    def search(self, query: str) -> List[IntelligenceEntry]:
        q = query.lower()
        return [e for e in self._entries.values()
                if q in e.category.lower() or q in str(e.data).lower()]

    def update(self, entry_id: str, data: Optional[Dict] = None,
               confidence: Optional[float] = None, score: Optional[float] = None) -> Optional[IntelligenceEntry]:
        entry = self._entries.get(entry_id)
        if entry is None:
            return None
        if data is not None:
            entry.data = data
        if confidence is not None:
            entry.confidence = confidence
        if score is not None:
            entry.score = score
        entry.version += 1
        entry.updated_at = time.time()
        return entry

    def delete(self, entry_id: str) -> bool:
        if entry_id in self._entries:
            self._remove_entry(entry_id)
            return True
        return False

    def _remove_entry(self, entry_id: str) -> None:
        entry = self._entries.pop(entry_id, None)
        if entry:
            for cat_ids in self._category_index.values():
                if entry_id in cat_ids:
                    cat_ids.remove(entry_id)

    @property
    def count(self) -> int:
        return len(self._entries)

    def stats(self) -> Dict[str, Any]:
        entries = list(self._entries.values())
        if not entries:
            return {"total": 0}
        avg_conf = sum(e.confidence for e in entries) / len(entries)
        return {
            "total": len(entries),
            "avg_confidence": round(avg_conf, 3),
            "categories": len(self._category_index),
            "tags": len(self._tag_index),
        }
