"""MemoryFallback — fallback strategies when primary memory stores fail."""
from __future__ import annotations

from typing import Any, Dict, List

from .models import MemoryEntry


class MemoryFallback:
    """Fallback strategies when primary memory operations fail."""

    def __init__(self) -> None:
        self._fallback_log: List[Dict[str, Any]] = []
        self._emergency_store: List[MemoryEntry] = []

    def emergency_store(self, entry: MemoryEntry) -> bool:
        self._emergency_store.append(entry)
        self._fallback_log.append({"action": "emergency_store", "entry_id": entry.entry_id})
        return True

    def get_emergency_entries(self) -> List[MemoryEntry]:
        return list(self._emergency_store)

    def replay_emergency(self, target_store: List[MemoryEntry]) -> int:
        count = len(self._emergency_store)
        target_store.extend(self._emergency_store)
        self._emergency_store.clear()
        return count

    def get_log(self) -> List[Dict[str, Any]]:
        return list(self._fallback_log)

    def clear(self) -> None:
        self._emergency_store.clear()
        self._fallback_log.clear()
