"""Bounded, indexed intelligence store with safe eviction and updates."""
from __future__ import annotations
import itertools
import time
from threading import RLock
from typing import Any, Dict, List, Optional

class IntelligenceEntry:
    __slots__ = ("entry_id","category","data","confidence","score","tags","source","version","created_at","updated_at","access_count","value")
    def __init__(self, category: str = "", data: Optional[Dict[str, Any]] = None) -> None:
        self.entry_id = f"ientry_{next(_ENTRY_COUNTER)}"
        self.category = category
        self.data = dict(data or {})
        self.confidence = 0.5
        self.score = 0.0
        self.tags: List[str] = []
        self.source = ""
        self.version = 1
        self.created_at = time.time()
        self.updated_at = self.created_at
        self.access_count = 0
        self.value = 0.5
    def to_dict(self) -> Dict[str, Any]:
        return {"entry_id":self.entry_id,"category":self.category,"confidence":round(self.confidence,3),"score":round(self.score,3),"tags":list(self.tags),"source":self.source,"version":self.version,"access_count":self.access_count}

_ENTRY_COUNTER = itertools.count(1)

class IntelligenceStore:
    """Bounded in-memory store; all indexes remain consistent."""
    def __init__(self, max_size: int = 1000) -> None:
        if max_size < 1:
            raise ValueError("max_size must be >= 1")
        self._entries: Dict[str, IntelligenceEntry] = {}
        self._category_index: Dict[str, List[str]] = {}
        self._tag_index: Dict[str, List[str]] = {}
        self._max_size = max_size
        self._lock = RLock()

    def store(self, category: str, data: Dict[str, Any], confidence: float = 0.5, score: float = 0.0, tags: Optional[List[str]] = None, source: str = "") -> IntelligenceEntry:
        if not 0.0 <= confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        with self._lock:
            entry = IntelligenceEntry(category, data)
            entry.confidence, entry.score = confidence, score
            entry.tags, entry.source = list(tags or []), source
            if len(self._entries) >= self._max_size:
                oldest = min(self._entries.values(), key=lambda e: (e.access_count, e.updated_at))
                self._remove_entry(oldest.entry_id)
            self._entries[entry.entry_id] = entry
            self._category_index.setdefault(category, []).append(entry.entry_id)
            for tag in entry.tags:
                self._tag_index.setdefault(tag, []).append(entry.entry_id)
            return entry

    def get(self, entry_id: str) -> Optional[IntelligenceEntry]:
        with self._lock:
            entry = self._entries.get(entry_id)
            if entry:
                entry.access_count += 1
            return entry

    def get_all(self) -> List[IntelligenceEntry]:
        with self._lock:
            return list(self._entries.values())

    def get_by_category(self, category: str) -> List[IntelligenceEntry]:
        with self._lock:
            return [self._entries[i] for i in self._category_index.get(category, []) if i in self._entries]

    def get_by_tag(self, tag: str) -> List[IntelligenceEntry]:
        with self._lock:
            return [self._entries[i] for i in self._tag_index.get(tag, []) if i in self._entries]

    def search(self, query: str) -> List[IntelligenceEntry]:
        q = query.lower().strip()
        if not q:
            return []
        with self._lock:
            return [e for e in self._entries.values() if q in e.category.lower() or q in str(e.data).lower()]

    def update(self, entry_id: str, data: Optional[Dict] = None, confidence: Optional[float] = None, score: Optional[float] = None, tags: Optional[List[str]] = None, source: Optional[str] = None) -> Optional[IntelligenceEntry]:
        with self._lock:
            entry = self._entries.get(entry_id)
            if entry is None:
                return None
            if confidence is not None and not 0.0 <= confidence <= 1.0:
                raise ValueError("confidence must be between 0 and 1")
            if data is not None: entry.data = dict(data)
            if confidence is not None: entry.confidence = confidence
            if score is not None: entry.score = score
            if source is not None: entry.source = source
            if tags is not None:
                for ids in self._tag_index.values():
                    if entry_id in ids: ids.remove(entry_id)
                entry.tags = list(tags)
                for tag in entry.tags: self._tag_index.setdefault(tag, []).append(entry_id)
                for tag in list(self._tag_index):
                    if not self._tag_index[tag]: self._tag_index.pop(tag)
            entry.version += 1
            entry.updated_at = time.time()
            return entry

    def delete(self, entry_id: str) -> bool:
        with self._lock:
            if entry_id not in self._entries: return False
            self._remove_entry(entry_id)
            return True

    def _remove_entry(self, entry_id: str) -> None:
        entry = self._entries.pop(entry_id, None)
        if entry is None: return
        ids = self._category_index.get(entry.category, [])
        if entry_id in ids: ids.remove(entry_id)
        if not ids: self._category_index.pop(entry.category, None)
        for tag in entry.tags:
            ids = self._tag_index.get(tag, [])
            if entry_id in ids: ids.remove(entry_id)
            if not ids: self._tag_index.pop(tag, None)

    @property
    def count(self) -> int:
        with self._lock: return len(self._entries)

    def stats(self) -> Dict[str, Any]:
        with self._lock:
            entries = list(self._entries.values())
            if not entries: return {"total": 0}
            return {"total":len(entries),"avg_confidence":round(sum(e.confidence for e in entries)/len(entries),3),"categories":len(self._category_index),"tags":len(self._tag_index)}
