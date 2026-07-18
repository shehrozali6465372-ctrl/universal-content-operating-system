"""cache_manager.py — Redis cache management."""
from __future__ import annotations
import time
from typing import Any, Dict, Optional


class CacheEntry:
    """Single cache entry."""
    __slots__ = ("key", "value", "created_at", "ttl", "hit_count")

    def __init__(self, key: str, value: str, ttl: float = 300.0) -> None:
        self.key = key
        self.value = value
        self.created_at: float = time.time()
        self.ttl = ttl
        self.hit_count: int = 0

    def is_expired(self) -> bool:
        return (time.time() - self.created_at) > self.ttl


class CacheManager:
    """Manages Redis-style caching with TTL and LRU."""

    def __init__(self, max_entries: int = 10000, default_ttl: float = 3600.0) -> None:
        self._cache: Dict[str, CacheEntry] = {}
        self._max_entries = max_entries
        self._default_ttl = default_ttl
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Optional[str]:
        entry = self._cache.get(key)
        if entry and not entry.is_expired():
            entry.hit_count += 1
            self._hits += 1
            return entry.value
        if entry:
            del self._cache[key]
        self._misses += 1
        return None

    def set(self, key: str, value: str, ttl: float = 0.0) -> bool:
        if len(self._cache) >= self._max_entries:
            self._evict_lru()
        self._cache[key] = CacheEntry(key, value, ttl or self._default_ttl)
        return True

    def delete(self, key: str) -> bool:
        return self._cache.pop(key, None) is not None

    def exists(self, key: str) -> bool:
        return key in self._cache

    def _evict_lru(self) -> None:
        if self._cache:
            lru_key = min(self._cache, key=lambda k: self._cache[k].hit_count)
            del self._cache[lru_key]

    def invalidate_pattern(self, pattern: str) -> int:
        import fnmatch
        keys = [k for k in self._cache if fnmatch.fnmatch(k, pattern)]
        for k in keys:
            del self._cache[k]
        return len(keys)

    def flush(self) -> int:
        count = len(self._cache)
        self._cache.clear()
        return count

    def get_stats(self) -> Dict[str, Any]:
        total = self._hits + self._misses
        return {"entries": len(self._cache), "max": self._max_entries,
                "hits": self._hits, "misses": self._misses,
                "hit_rate": self._hits / max(1, total)}
