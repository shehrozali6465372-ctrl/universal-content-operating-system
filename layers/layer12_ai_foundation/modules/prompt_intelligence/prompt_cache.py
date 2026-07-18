"""PromptCache — cache optimized and rendered prompts."""
from __future__ import annotations

import time
from typing import Any, Dict, Optional


class PromptCache:
    """Cache for optimized and rendered prompts."""

    def __init__(self, max_size: int = 500, ttl: int = 3600) -> None:
        self.max_size = max_size
        self.ttl = ttl
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Optional[str]:
        entry = self._cache.get(key)
        if entry and (time.time() - entry["ts"]) < self.ttl:
            self._hits += 1
            return entry["value"]
        self._misses += 1
        return None

    def set(self, key: str, value: str) -> None:
        if len(self._cache) >= self.max_size:
            oldest = min(self._cache, key=lambda k: self._cache[k]["ts"])
            del self._cache[oldest]
        self._cache[key] = {"value": value, "ts": time.time()}

    def invalidate(self, key: str) -> bool:
        return self._cache.pop(key, None) is not None

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
