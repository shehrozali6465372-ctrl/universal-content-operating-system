"""
Cache Manager
Layer 2: Research Engine — Module 5

In-memory cache for knowledge entries:
- TTL-based expiration
- LRU eviction
- Cache hit/miss tracking
- Cache size management
"""

from collections import OrderedDict
from datetime import datetime, timezone, timedelta
from typing import Optional


class CacheEntry:
    """A single cache entry with TTL."""

    __slots__ = ("key", "value", "created_at", "expires_at", "access_count")

    def __init__(self, key: str, value: dict, ttl_seconds: int = 3600):
        self.key = key
        self.value = value
        self.created_at = datetime.now(timezone.utc)
        self.expires_at = self.created_at + timedelta(seconds=ttl_seconds)
        self.access_count = 0

    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) > self.expires_at


class KnowledgeCache:
    """LRU cache with TTL for knowledge entries."""

    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Optional[dict]:
        """Get a value from cache."""
        entry = self._cache.get(key)
        if entry is None:
            self._misses += 1
            return None
        if entry.is_expired():
            del self._cache[key]
            self._misses += 1
            return None
        # Move to end (most recently used)
        self._cache.move_to_end(key)
        entry.access_count += 1
        self._hits += 1
        return entry.value

    def put(self, key: str, value: dict, ttl: Optional[int] = None):
        """Put a value into cache."""
        if key in self._cache:
            self._cache.move_to_end(key)
        self._cache[key] = CacheEntry(key, value, ttl or self._default_ttl)
        # Evict LRU if over size
        while len(self._cache) > self._max_size:
            self._cache.popitem(last=False)

    def delete(self, key: str) -> bool:
        if key in self._cache:
            del self._cache[key]
            return True
        return False

    def exists(self, key: str) -> bool:
        entry = self._cache.get(key)
        if entry is None:
            return False
        if entry.is_expired():
            del self._cache[key]
            return False
        return True

    def cleanup(self) -> int:
        """Remove expired entries. Returns count removed."""
        expired = [k for k, v in self._cache.items() if v.is_expired()]
        for k in expired:
            del self._cache[k]
        return len(expired)

    def clear(self):
        self._cache.clear()
        self._hits = 0
        self._misses = 0

    def size(self) -> int:
        return len(self._cache)

    def stats(self) -> dict:
        total = self._hits + self._misses
        return {
            "size": len(self._cache),
            "max_size": self._max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(self._hits / total, 3) if total > 0 else 0.0,
        }
