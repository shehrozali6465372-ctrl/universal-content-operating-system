"""CacheManager — Cache research, prompts, analytics, memory, predictions."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional


class CacheEntry:
    """A cache entry with TTL."""

    __slots__ = ("key", "value", "category", "created_at", "expires_at", "hit_count")

    def __init__(self, key: str = "", value: Any = None,
                 ttl_seconds: int = 3600) -> None:
        self.key = key
        self.value = value
        self.category: str = ""
        self.created_at: float = time.time()
        self.expires_at: float = time.time() + ttl_seconds
        self.hit_count: int = 0

    def is_expired(self) -> bool:
        return time.time() > self.expires_at


class CacheManager:
    """Cache research, prompts, analytics, memory, and predictions."""

    def __init__(self, max_entries: int = 10000) -> None:
        self._max_entries = max_entries
        self._cache: Dict[str, CacheEntry] = {}
        self._hits: int = 0
        self._misses: int = 0

    def set(self, key: str, value: Any, category: str = "general",
            ttl_seconds: int = 3600) -> None:
        if len(self._cache) >= self._max_entries:
            self._evict()
        entry = CacheEntry(key, value, ttl_seconds)
        entry.category = category
        self._cache[key] = entry

    def get(self, key: str) -> Optional[Any]:
        entry = self._cache.get(key)
        if entry is None:
            self._misses += 1
            return None
        if entry.is_expired():
            del self._cache[key]
            self._misses += 1
            return None
        entry.hit_count += 1
        self._hits += 1
        return entry.value

    def delete(self, key: str) -> bool:
        return self._cache.pop(key, None) is not None

    def clear(self, category: str = "") -> int:
        if category:
            to_remove = [k for k, v in self._cache.items() if v.category == category]
            for k in to_remove:
                del self._cache[k]
            return len(to_remove)
        count = len(self._cache)
        self._cache.clear()
        return count

    def has(self, key: str) -> bool:
        entry = self._cache.get(key)
        return entry is not None and not entry.is_expired()

    def get_hit_rate(self) -> float:
        total = self._hits + self._misses
        if total == 0:
            return 0.0
        return round(self._hits / total, 3)

    def get_by_category(self, category: str) -> List[str]:
        return [k for k, v in self._cache.items()
                if v.category == category and not v.is_expired()]

    def get_stats(self) -> Dict[str, Any]:
        return {"total_entries": len(self._cache),
                "hits": self._hits, "misses": self._misses,
                "hit_rate": self.get_hit_rate()}

    def _evict(self) -> None:
        if self._cache:
            oldest_key = min(self._cache, key=lambda k: self._cache[k].created_at)
            del self._cache[oldest_key]
