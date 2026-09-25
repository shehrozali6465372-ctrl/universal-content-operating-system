"""Thread-safe TTL cache for Layer 3 intelligence results."""
from __future__ import annotations
import copy
import time
from threading import RLock
from typing import Any, Dict, List, Optional

class CachedResult:
    __slots__ = ("key", "data", "created_at", "expires_at", "last_accessed", "hit_count")
    def __init__(self, key: str, data: Any, ttl_seconds: int) -> None:
        now = time.monotonic()
        self.key = key
        self.data = copy.deepcopy(data)
        self.created_at = now
        self.expires_at = now + ttl_seconds if ttl_seconds else float("inf")
        self.last_accessed = now
        self.hit_count = 0
    def to_dict(self) -> dict:
        return {"key": self.key, "hit_count": self.hit_count, "created_at": self.created_at, "expires_at": self.expires_at}

class IntelligenceCache:
    """Bounded TTL cache with defensive copies and LRU eviction."""
    def __init__(self, max_size: int = 500, ttl_seconds: int = 3600) -> None:
        if max_size < 1:
            raise ValueError("max_size must be >= 1")
        if ttl_seconds < 0:
            raise ValueError("ttl_seconds must be >= 0")
        self._cache: Dict[str, CachedResult] = {}
        self._max_size = max_size
        self._ttl = ttl_seconds
        self._lock = RLock()

    def store(self, key: str, data: Any) -> None:
        if not key:
            raise ValueError("cache key must not be empty")
        with self._lock:
            now = time.monotonic()
            self._purge_expired(now)
            if key not in self._cache and len(self._cache) >= self._max_size:
                oldest = min(self._cache.values(), key=lambda c: c.last_accessed)
                self._cache.pop(oldest.key, None)
            self._cache[key] = CachedResult(key, data, self._ttl)

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            entry = self._cache.get(key)
            if entry is None or entry.expires_at <= time.monotonic():
                self._cache.pop(key, None)
                return None
            entry.hit_count += 1
            entry.last_accessed = time.monotonic()
            return copy.deepcopy(entry.data)

    def has(self, key: str) -> bool:
        return self.get(key) is not None

    def remove(self, key: str) -> bool:
        with self._lock:
            return self._cache.pop(key, None) is not None

    def size(self) -> int:
        with self._lock:
            self._purge_expired(time.monotonic())
            return len(self._cache)

    def hit_rate(self) -> float:
        with self._lock:
            self._purge_expired(time.monotonic())
            hits = sum(c.hit_count for c in self._cache.values())
            requests = hits + len(self._cache)
            return round(hits / requests, 3) if requests else 0.0

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()

    def keys(self) -> List[str]:
        with self._lock:
            self._purge_expired(time.monotonic())
            return list(self._cache.keys())

    def _purge_expired(self, now: float) -> None:
        for key, entry in list(self._cache.items()):
            if entry.expires_at <= now:
                self._cache.pop(key, None)
