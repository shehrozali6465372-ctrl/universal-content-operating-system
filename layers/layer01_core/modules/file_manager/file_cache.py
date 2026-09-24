"""
File Cache Module
Layer 1: Core System — Module 8

In-memory LRU cache for frequently accessed files.
"""

from collections import OrderedDict
from typing import Any, Optional
from threading import RLock


class FileCache:
    """LRU cache for file content."""

    def __init__(self, max_size: int = 100):
        if not isinstance(max_size, int) or isinstance(max_size, bool) or max_size < 1:
            raise ValueError("max_size must be a positive integer")
        self._cache: OrderedDict[str, dict] = OrderedDict()
        self._max_size = max_size
        self._hits = 0
        self._misses = 0
        self._lock = RLock()

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
                self._hits += 1
                return self._cache[key]["content"]
            self._misses += 1
            return None

    def set(self, key: str, content: Any) -> None:
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
                self._cache[key]["content"] = content
            else:
                self._cache[key] = {"content": content}
                if len(self._cache) > self._max_size:
                    self._cache.popitem(last=False)

    def has(self, key: str) -> bool:
        with self._lock:
            return key in self._cache

    def invalidate(self, key: str) -> None:
        with self._lock:
            self._cache.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()

    @property
    def size(self) -> int:
        with self._lock:
            return len(self._cache)

    @property
    def hit_rate(self) -> float:
        with self._lock:
            total = self._hits + self._misses
            return self._hits / total if total > 0 else 0.0

    def stats(self) -> dict:
        with self._lock:
            total = self._hits + self._misses
            return {
                "size": len(self._cache),
                "max_size": self._max_size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": self._hits / total if total else 0.0,
            }
