"""memory_compaction.py — Memory compaction and cleanup."""
from __future__ import annotations
import time
from typing import Any, Dict, List
from layers.layer13_persistence.modules.ai_memory_persistence.base_memory_store import BaseMemoryStore


class MemoryCompactor:
    """Compacts and cleans up memory stores."""

    def __init__(self) -> None:
        self._compactions: List[Dict[str, Any]] = []

    def compact(self, store: BaseMemoryStore, max_age_seconds: float = 86400.0) -> Dict[str, Any]:
        before = store.count()
        now = time.time()
        removed = 0
        for key in list(store.list_keys()):
            entry = store._store.get(key)
            if entry and (now - entry.created_at) > max_age_seconds and entry.access_count == 0:
                store._store.pop(key, None)
                removed += 1
        result = {"before": before, "removed": removed, "after": store.count(),
                  "timestamp": time.time()}
        self._compactions.append(result)
        return result

    def compact_by_access(self, store: BaseMemoryStore, min_access: int = 1) -> Dict[str, Any]:
        before = store.count()
        removed = 0
        for key in list(store.list_keys()):
            entry = store._store.get(key)
            if entry and entry.access_count < min_access:
                store._store.pop(key, None)
                removed += 1
        return {"before": before, "removed": removed, "after": store.count()}

    def get_history(self) -> List[Dict[str, Any]]:
        return list(self._compactions)

    def stats(self) -> Dict[str, Any]:
        total_removed = sum(c["removed"] for c in self._compactions)
        return {"compactions": len(self._compactions), "total_removed": total_removed}
