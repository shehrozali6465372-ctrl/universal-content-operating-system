"""garbage_collector.py — Storage garbage collection."""
from __future__ import annotations
from typing import Dict


class GarbageCollector:
    """Collects garbage from storage."""

    def __init__(self) -> None:
        self._collected: Dict[str, int] = {}
        self._total_collected: int = 0

    def collect(self, store_name: str, orphaned: int) -> int:
        self._collected[store_name] = self._collected.get(store_name, 0) + orphaned
        self._total_collected += orphaned
        return orphaned

    def get_stats(self, store_name: str = "") -> int:
        if store_name:
            return self._collected.get(store_name, 0)
        return self._total_collected

    def get_all_stats(self) -> Dict[str, int]:
        return dict(self._collected)
