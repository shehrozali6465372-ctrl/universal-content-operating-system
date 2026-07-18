"""embedding_cache.py — Embedding cache for performance."""
from __future__ import annotations
import hashlib
import time
from typing import Any, Dict, List, Optional


class EmbeddingCache:
    """Caches embeddings to avoid recomputation."""

    def __init__(self, max_size: int = 10000, ttl_seconds: float = 86400.0) -> None:
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._max_size = max_size
        self._ttl = ttl_seconds
        self._hits = 0
        self._misses = 0

    def _make_key(self, text: str, model: str) -> str:
        return hashlib.md5(f"{model}:{text}".encode()).hexdigest()

    def get(self, text: str, model: str = "default") -> Optional[List[float]]:
        key = self._make_key(text, model)
        entry = self._cache.get(key)
        if entry and (time.time() - entry["time"]) < self._ttl:
            entry["hits"] += 1
            self._hits += 1
            return entry["vector"]
        self._misses += 1
        return None

    def set(self, text: str, vector: List[float], model: str = "default") -> None:
        if len(self._cache) >= self._max_size:
            oldest = min(self._cache, key=lambda k: self._cache[k]["time"])
            del self._cache[oldest]
        key = self._make_key(text, model)
        self._cache[key] = {"vector": vector, "time": time.time(), "hits": 0}

    def invalidate(self, text: str, model: str = "default") -> bool:
        key = self._make_key(text, model)
        return self._cache.pop(key, None) is not None

    def flush(self) -> int:
        count = len(self._cache)
        self._cache.clear()
        return count

    def get_stats(self) -> Dict[str, Any]:
        total = self._hits + self._misses
        return {"entries": len(self._cache), "hits": self._hits, "misses": self._misses,
                "hit_rate": self._hits / max(1, total)}
