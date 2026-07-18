"""MultiModelCache — cache multi-model results."""
from __future__ import annotations

import time
from typing import Any, Dict, Optional


class MultiModelCache:
    """Cache for multi-model intelligence results."""

    def __init__(self, max_size: int = 500, ttl: int = 3600) -> None:
        self.max_size = max_size
        self.ttl = ttl
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._hits = 0
        self._misses = 0

    def _make_key(self, prompt: str, models: list) -> str:
        model_str = ",".join(sorted(models))
        return f"{hash(prompt) % 10**8}:{hash(model_str) % 10**6}"

    def get(self, prompt: str, models: list) -> Optional[Dict[str, Any]]:
        key = self._make_key(prompt, models)
        entry = self._cache.get(key)
        if entry and (time.time() - entry["timestamp"]) < self.ttl:
            self._hits += 1
            return entry["data"]
        self._misses += 1
        return None

    def set(self, prompt: str, models: list, data: Dict[str, Any]) -> None:
        if len(self._cache) >= self.max_size:
            # Evict oldest
            oldest = min(self._cache, key=lambda k: self._cache[k]["timestamp"])
            del self._cache[oldest]
        key = self._make_key(prompt, models)
        self._cache[key] = {"data": data, "timestamp": time.time()}

    def invalidate(self, prompt: str, models: list) -> bool:
        key = self._make_key(prompt, models)
        if key in self._cache:
            del self._cache[key]
            return True
        return False

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
