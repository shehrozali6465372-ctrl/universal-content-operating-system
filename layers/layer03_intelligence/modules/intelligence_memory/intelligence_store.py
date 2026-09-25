"""Thread-safe bounded intelligence store with isolated snapshots and consistent indexes."""
from __future__ import annotations
import copy
import math
import time
from threading import RLock
from typing import Any, Dict, List, Optional
from uuid import uuid4


class IntelligenceEntry:
    __slots__ = (
        "entry_id", "category", "data", "confidence", "score", "tags",
        "source", "version", "created_at", "updated_at", "access_count", "value",
    )

    def __init__(self, category: str = "", data: Optional[Dict[str, Any]] = None) -> None:
        self.entry_id = f"ientry_{uuid4().hex}"
        self.category = category
        self.data = copy.deepcopy(data or {})
        self.confidence = 0.5
        self.score = 0.0
        self.tags: List[str] = []
        self.source = ""
        self.version = 1
        now = time.time()
        self.created_at = now
        self.updated_at = now
        self.access_count = 0
        self.value = 0.5

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "category": self.category,
            "confidence": round(self.confidence, 3),
            "score": round(self.score, 3),
            "tags": list(self.tags),
            "source": self.source,
            "version": self.version,
            "access_count": self.access_count,
        }


class IntelligenceStore:
    """Bounded store with thread-safe CRUD and consistent category/tag indexes."""

    def __init__(self, max_size: int = 1000) -> None:
        if max_size < 1:
            raise ValueError("max_size must be >= 1")
        self._entries: Dict[str, IntelligenceEntry] = {}
        self._category_index: Dict[str, List[str]] = {}
        self._tag_index: Dict[str, List[str]] = {}
        self._max_size = max_size
        self._lock = RLock()

    @staticmethod
    def _validate_metrics(confidence: Optional[float], score: Optional[float]) -> None:
        if confidence is not None and (
            not math.isfinite(confidence) or not 0.0 <= confidence <= 1.0
        ):
            raise ValueError("confidence must be finite and between 0 and 1")
        if score is not None and not math.isfinite(score):
            raise ValueError("score must be finite")

    @staticmethod
    def _snapshot(entry: IntelligenceEntry) -> IntelligenceEntry:
        return copy.deepcopy(entry)

    def store(
        self,
        category: str,
        data: Dict[str, Any],
        confidence: float = 0.5,
        score: float = 0.0,
        tags: Optional[List[str]] = None,
        source: str = "",
    ) -> IntelligenceEntry:
        self._validate_metrics(confidence, score)
        with self._lock:
            entry = IntelligenceEntry(category, data)
            entry.confidence = confidence
            entry.score = score
            entry.tags = list(tags or [])
            entry.source = source
            if len(self._entries) >= self._max_size:
                oldest = min(
                    self._entries.values(),
                    key=lambda e: (e.access_count, e.updated_at),
                )
                self._remove_entry(oldest.entry_id)
            self._entries[entry.entry_id] = entry
            self._category_index.setdefault(category, []).append(entry.entry_id)
            for tag in entry.tags:
                self._tag_index.setdefault(tag, []).append(entry.entry_id)
            return self._snapshot(entry)

    def get(self, entry_id: str) -> Optional[IntelligenceEntry]:
        with self._lock:
            entry = self._entries.get(entry_id)
            if entry is None:
                return None
            entry.access_count += 1
            return self._snapshot(entry)

    def get_all(self) -> List[IntelligenceEntry]:
        with self._lock:
            return [self._snapshot(entry) for entry in self._entries.values()]

    def get_by_category(self, category: str) -> List[IntelligenceEntry]:
        with self._lock:
            return [
                self._snapshot(self._entries[i])
                for i in self._category_index.get(category, [])
                if i in self._entries
            ]

    def get_by_tag(self, tag: str) -> List[IntelligenceEntry]:
        with self._lock:
            return [
                self._snapshot(self._entries[i])
                for i in self._tag_index.get(tag, [])
                if i in self._entries
            ]

    def search(self, query: str) -> List[IntelligenceEntry]:
        q = query.lower().strip()
        if not q:
            return []
        with self._lock:
            return [
                self._snapshot(entry)
                for entry in self._entries.values()
                if q in entry.category.lower() or q in str(entry.data).lower()
            ]

    def update(
        self,
        entry_id: str,
        data: Optional[Dict[str, Any]] = None,
        confidence: Optional[float] = None,
        score: Optional[float] = None,
        tags: Optional[List[str]] = None,
        source: Optional[str] = None,
    ) -> Optional[IntelligenceEntry]:
        self._validate_metrics(confidence, score)
        with self._lock:
            entry = self._entries.get(entry_id)
            if entry is None:
                return None
            if data is not None:
                entry.data = copy.deepcopy(data)
            if confidence is not None:
                entry.confidence = confidence
            if score is not None:
                entry.score = score
            if source is not None:
                entry.source = source
            if tags is not None:
                for ids in self._tag_index.values():
                    ids[:] = [i for i in ids if i != entry_id]
                entry.tags = list(tags)
                for tag in entry.tags:
                    self._tag_index.setdefault(tag, []).append(entry_id)
                self._tag_index = {k: v for k, v in self._tag_index.items() if v}
            entry.version += 1
            entry.updated_at = time.time()
            return self._snapshot(entry)

    def delete(self, entry_id: str) -> bool:
        with self._lock:
            if entry_id not in self._entries:
                return False
            self._remove_entry(entry_id)
            return True

    def _remove_entry(self, entry_id: str) -> None:
        entry = self._entries.pop(entry_id, None)
        if entry is None:
            return
        ids = self._category_index.get(entry.category, [])
        if entry_id in ids:
            ids.remove(entry_id)
        if not ids:
            self._category_index.pop(entry.category, None)
        for tag in entry.tags:
            tids = self._tag_index.get(tag, [])
            if entry_id in tids:
                tids.remove(entry_id)
            if not tids:
                self._tag_index.pop(tag, None)

    @property
    def count(self) -> int:
        with self._lock:
            return len(self._entries)

    def stats(self) -> Dict[str, Any]:
        with self._lock:
            entries = list(self._entries.values())
            if not entries:
                return {"total": 0}
            return {
                "total": len(entries),
                "avg_confidence": round(
                    sum(e.confidence for e in entries) / len(entries), 3
                ),
                "categories": len(self._category_index),
                "tags": len(self._tag_index),
            }
