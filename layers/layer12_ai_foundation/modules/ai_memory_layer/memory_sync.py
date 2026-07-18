"""MemorySync — synchronize memory across stores."""
from __future__ import annotations

import time
from typing import Any, Dict, List

from .models import MemoryEntry


class MemorySync:
    """Synchronize memory across multiple stores."""

    def __init__(self) -> None:
        self._sync_log: List[Dict[str, Any]] = []
        self._last_sync: float = 0.0

    def sync(self, source: List[MemoryEntry], target: List[MemoryEntry]) -> Dict[str, Any]:
        source_ids = {e.entry_id for e in source}
        target_ids = {e.entry_id for e in target}
        to_add = [e for e in source if e.entry_id not in target_ids]
        to_remove = [e for e in target if e.entry_id not in source_ids]

        result = {"added": len(to_add), "removed": len(to_remove),
                  "unchanged": len(source) - len(to_add)}
        target.extend(to_add)
        for entry in to_remove:
            target[:] = [e for e in target if e.entry_id != entry.entry_id]

        self._last_sync = time.time()
        self._sync_log.append(result)
        return result

    def merge(self, store_a: List[MemoryEntry], store_b: List[MemoryEntry]) -> List[MemoryEntry]:
        seen = set()
        merged = []
        for entry in store_a + store_b:
            if entry.entry_id not in seen:
                seen.add(entry.entry_id)
                merged.append(entry)
        return merged

    def get_last_sync_time(self) -> float:
        return self._last_sync

    def get_sync_log(self) -> List[Dict[str, Any]]:
        return list(self._sync_log)
