"""LLMMemory — Cache LLM responses for reuse."""
from __future__ import annotations
import time
from typing import Any, Dict, Optional

class LLMCacheEntry:
    __slots__ = ("key", "response", "created_at", "ttl", "hit_count")
    def __init__(self, key: str = "", response: str = "", ttl: int = 300) -> None:
        self.key = key
        self.response = response
        self.created_at: float = time.time()
        self.ttl = ttl
        self.hit_count: int = 0
    def is_expired(self) -> bool:
        return (time.time() - self.created_at) > self.ttl

class LLMMemory:
    def __init__(self, max_entries: int = 1000) -> None:
        self._max = max_entries
        self._cache: Dict[str, LLMCacheEntry] = {}
        self._hits = 0
        self._misses = 0
    def get(self, key: str) -> Optional[str]:
        entry = self._cache.get(key)
        if entry and not entry.is_expired():
            entry.hit_count += 1
            self._hits += 1
            return entry.response
        self._misses += 1
        return None
    def set(self, key: str, response: str, ttl: int = 300) -> None:
        if len(self._cache) >= self._max:
            oldest = min(self._cache, key=lambda k: self._cache[k].created_at)
            del self._cache[oldest]
        self._cache[key] = LLMCacheEntry(key, response, ttl)
    def delete(self, key: str) -> bool:
        return self._cache.pop(key, None) is not None
    def clear(self) -> int:
        count = len(self._cache)
        self._cache.clear()
        return count
    def get_hit_rate(self) -> float:
        total = self._hits + self._misses
        return round(self._hits / max(1, total), 3)
    def get_stats(self) -> Dict[str, Any]:
        return {"entries": len(self._cache), "hits": self._hits,
                "misses": self._misses, "hit_rate": self.get_hit_rate()}
