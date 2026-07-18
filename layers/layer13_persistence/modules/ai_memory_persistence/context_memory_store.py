"""context_memory_store.py — Context memory persistence."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from layers.layer13_persistence.modules.ai_memory_persistence.base_memory_store import BaseMemoryStore, MemoryEntry


class ContextMemoryStore(BaseMemoryStore):
    """Stores execution and session context."""

    def __init__(self, max_entries: int = 5000) -> None:
        super().__init__("context", max_entries)
        self._contexts: Dict[str, Dict[str, Any]] = {}

    def store(self, key: str, value: Any, metadata: Dict[str, Any] = None) -> MemoryEntry:
        entry = MemoryEntry(key, value, "context")
        if metadata:
            entry.metadata = metadata
        self._store[key] = entry
        return entry

    def retrieve(self, key: str) -> Optional[MemoryEntry]:
        entry = self._store.get(key)
        if entry:
            entry.access_count += 1
        return entry

    def save_context(self, context_id: str, context: Dict[str, Any]) -> None:
        self._contexts[context_id] = context

    def load_context(self, context_id: str) -> Optional[Dict[str, Any]]:
        return self._contexts.get(context_id)

    def list_contexts(self) -> List[str]:
        return list(self._contexts.keys())

    def delete_context(self, context_id: str) -> bool:
        return self._contexts.pop(context_id, None) is not None

    def stats(self) -> Dict[str, Any]:
        base = super().stats()
        base["contexts"] = len(self._contexts)
        return base
