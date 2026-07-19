"""ReasoningCache — cache reasoning results for reuse."""
from __future__ import annotations

import time
from typing import Any, Dict, Optional


class ReasoningCache:
    """Cache reasoning results for efficient reuse."""

    def __init__(self, max_size: int = 200, ttl: int = 3600) -> None:
        self.max_size = max_size
        self.ttl = ttl
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._hits = 0
        self._misses = 0

    def get(self, query: str) -> Optional[Dict[str, Any]]:
        entry = self._cache.get(query)
        if entry and (time.time() - entry["ts"]) < self.ttl:
            self._hits += 1
            return entry["data"]
        self._misses += 1
        return None

    def set(self, query: str, data: Dict[str, Any]) -> None:
        if len(self._cache) >= self.max_size:
            oldest = min(self._cache, key=lambda k: self._cache[k]["ts"])
            del self._cache[oldest]
        self._cache[query] = {"data": data, "ts": time.time()}

    def invalidate(self, query: str) -> bool:
        return self._cache.pop(query, None) is not None

    def clear(self) -> None:
        self._cache.clear()
        self._hits = 0
        self._misses = 0

    @property
    def hit_rate(self) -> float:
        total = self._hits + self._misses
        return self._hits / total if total > 0 else 0.0

    def stats(self) -> Dict[str, Any]:
        return {"size": len(self._cache), "hits": self._hits,
                "misses": self._misses, "hit_rate": round(self.hit_rate, 4)}
