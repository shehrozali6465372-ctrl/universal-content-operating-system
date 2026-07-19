"""CacheLayer — in-memory cache with TTL and eviction."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional


class CacheEntry:
    __slots__ = ("key", "value", "ttl", "created_at", "access_count", "metadata")

    def __init__(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        self.key = key
        self.value = value
        self.ttl = ttl
        self.created_at = time.time()
        self.access_count = 0
        self.metadata: Dict[str, Any] = {}

    def is_expired(self) -> bool:
        if self.ttl is None:
            return False
        return (time.time() - self.created_at) > self.ttl

    def to_dict(self) -> Dict[str, Any]:
        return {"key": self.key, "access_count": self.access_count,
                "expired": self.is_expired()}


class CacheLayer:
    def __init__(self, max_size: int = 1000) -> None:
        self._cache: Dict[str, CacheEntry] = {}
        self._max_size = max_size
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Any:
        entry = self._cache.get(key)
        if entry and not entry.is_expired():
            entry.access_count += 1
            self._hits += 1
            return entry.value
        self._misses += 1
        if entry:
            del self._cache[key]
        return None

    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        if len(self._cache) >= self._max_size:
            self._evict_lru()
        self._cache[key] = CacheEntry(key, value, ttl)

    def has(self, key: str) -> bool:
        entry = self._cache.get(key)
        return entry is not None and not entry.is_expired()

    def delete(self, key: str) -> bool:
        if key in self._cache:
            del self._cache[key]
            return True
        return False

    def clear(self) -> int:
        count = len(self._cache)
        self._cache.clear()
        return count

    def cleanup_expired(self) -> int:
        expired = [k for k, e in self._cache.items() if e.is_expired()]
        for k in expired:
            del self._cache[k]
        return len(expired)

    def _evict_lru(self) -> None:
        if not self._cache:
            return
        lru_key = min(self._cache, key=lambda k: self._cache[k].access_count)
        del self._cache[lru_key]

    def keys(self) -> List[str]:
        return [k for k, e in self._cache.items() if not e.is_expired()]

    def size(self) -> int:
        return len(self._cache)

    def stats(self) -> Dict[str, Any]:
        total = self._hits + self._misses
        return {"size": self.size(), "max_size": self._max_size,
                "hits": self._hits, "misses": self._misses,
                "hit_rate": round(self._hits / max(total, 1), 3)}
