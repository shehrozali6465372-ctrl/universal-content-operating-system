"""cache_coordinator.py — Cache coordination."""
from __future__ import annotations
from typing import Any, Dict, List


class CacheCoordinator:
    """Coordinates cache invalidation across stores."""

    def __init__(self) -> None:
        self._invalidations: List[Dict[str, Any]] = []
        self._patterns: Dict[str, List[str]] = {}

    def invalidate(self, store: str, pattern: str) -> None:
        self._invalidations.append({"store": store, "pattern": pattern})
        if store not in self._patterns:
            self._patterns[store] = []
        self._patterns[store].append(pattern)

    def invalidate_all(self) -> int:
        count = len(self._invalidations)
        self._invalidations.clear()
        self._patterns.clear()
        return count

    def get_pending(self) -> List[Dict[str, Any]]:
        return list(self._invalidations)

    def get_patterns(self, store: str) -> List[str]:
        return list(self._patterns.get(store, []))

    def stats(self) -> Dict[str, Any]:
        return {"pending": len(self._invalidations), "stores": len(self._patterns)}
