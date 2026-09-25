"""CacheManager — bounded TTL cache with deterministic eviction."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional


class CacheEntry:
    """A cache entry with TTL."""

    __slots__ = ("key", "value", "category", "created_at", "expires_at", "hit_count")

    def __init__(self, key: str, value: Any, ttl_seconds: float) -> None:
        self.key = key
        self.value = value
        self.category = ""
        self.created_at = time.time()
        self.expires_at = self.created_at + ttl_seconds
        self.hit_count = 0

    def is_expired(self) -> bool:
        return time.time() >= self.expires_at


class CacheManager:
    """Cache research, prompts, analytics, memory, and predictions."""

    def __init__(self, max_entries: int = 10000) -> None:
        if max_entries <= 0:
            raise ValueError("max_entries must be positive")
        self._max_entries = max_entries
        self._cache: Dict[str, CacheEntry] = {}
        self._hits = 0
        self._misses = 0

    def set(self, key: str, value: Any, category: str = "general",
            ttl_seconds: float = 3600) -> None:
        if not key or ttl_seconds <= 0:
            raise ValueError("key and positive ttl_seconds are required")
        if key not in self._cache and len(self._cache) >= self._max_entries:
            self._evict()
        entry = CacheEntry(key, value, ttl_seconds)
        entry.category = category
        self._cache[key] = entry

    def get(self, key: str) -> Optional[Any]:
        entry = self._cache.get(key)
        if entry is None or entry.is_expired():
            if entry is not None:
                self._cache.pop(key, None)
            self._misses += 1
            return None
        entry.hit_count += 1
        self._hits += 1
        return entry.value

    def delete(self, key: str) -> bool:
        return self._cache.pop(key, None) is not None

    def clear(self, category: str = "") -> int:
        if category:
            keys = [key for key, value in self._cache.items() if value.category == category]
            for key in keys:
                self._cache.pop(key, None)
            return len(keys)
        count = len(self._cache)
        self._cache.clear()
        return count

    def has(self, key: str) -> bool:
        return self.get(key) is not None

    def get_hit_rate(self) -> float:
        total = self._hits + self._misses
        return round(self._hits / total, 3) if total else 0.0

    def get_by_category(self, category: str) -> List[str]:
        return [key for key, value in self._cache.items()
                if value.category == category and not value.is_expired()]

    def get_stats(self) -> Dict[str, Any]:
        return {"total_entries": len(self._cache), "hits": self._hits,
                "misses": self._misses, "hit_rate": self.get_hit_rate()}

    def _evict(self) -> None:
        expired = [key for key, entry in self._cache.items() if entry.is_expired()]
        for key in expired:
            self._cache.pop(key, None)
        if len(self._cache) >= self._max_entries and self._cache:
            oldest_key = min(self._cache, key=lambda key: self._cache[key].created_at)
            self._cache.pop(oldest_key, None)
