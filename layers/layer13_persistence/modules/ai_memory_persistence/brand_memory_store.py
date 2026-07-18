"""brand_memory_store.py — Brand memory persistence."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from layers.layer13_persistence.modules.ai_memory_persistence.base_memory_store import BaseMemoryStore, MemoryEntry


class BrandMemoryStore(BaseMemoryStore):
    """Stores brand guidelines, voice, and style memories."""

    def __init__(self, max_entries: int = 2000) -> None:
        super().__init__("brand", max_entries)
        self._guidelines: Dict[str, str] = {}
        self._voice_samples: List[Dict[str, Any]] = []

    def store(self, key: str, value: Any, metadata: Dict[str, Any] = None) -> MemoryEntry:
        entry = MemoryEntry(key, value, "brand")
        if metadata:
            entry.metadata = metadata
        self._store[key] = entry
        return entry

    def retrieve(self, key: str) -> Optional[MemoryEntry]:
        entry = self._store.get(key)
        if entry:
            entry.access_count += 1
        return entry

    def set_guideline(self, category: str, text: str) -> None:
        self._guidelines[category] = text

    def get_guideline(self, category: str) -> Optional[str]:
        return self._guidelines.get(category)

    def get_all_guidelines(self) -> Dict[str, str]:
        return dict(self._guidelines)

    def add_voice_sample(self, sample: Dict[str, Any]) -> None:
        self._voice_samples.append(sample)

    def get_voice_samples(self, limit: int = 10) -> List[Dict[str, Any]]:
        return self._voice_samples[-limit:]

    def stats(self) -> Dict[str, Any]:
        base = super().stats()
        base["guidelines"] = len(self._guidelines)
        base["voice_samples"] = len(self._voice_samples)
        return base
