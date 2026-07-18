"""provider_cache.py — Provider response caching."""
from __future__ import annotations
import time
from typing import Any, Dict, Optional


class ProviderCache:
    """Caches provider responses to avoid duplicate API calls."""

    def __init__(self, max_entries: int = 1000, ttl_seconds: float = 3600.0) -> None:
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._max_entries = max_entries
        self._ttl = ttl_seconds
        self._hits = 0
        self._misses = 0

    def _make_key(self, provider: str, model: str, prompt: str) -> str:
        return f"{provider}:{model}:{prompt[:500]}"

    def get(self, provider: str, model: str, prompt: str) -> Optional[str]:
        key = self._make_key(provider, model, prompt)
        entry = self._cache.get(key)
        if entry:
            if time.time() - entry["created_at"] < self._ttl:
                self._hits += 1
                return entry["content"]
            del self._cache[key]
        self._misses += 1
        return None

    def set(self, provider: str, model: str, prompt: str, content: str) -> None:
        if len(self._cache) >= self._max_entries:
            oldest_key = min(self._cache, key=lambda k: self._cache[k]["created_at"])
            del self._cache[oldest_key]
        key = self._make_key(provider, model, prompt)
        self._cache[key] = {"content": content, "created_at": time.time()}

    def invalidate(self, provider: str = "", model: str = "") -> int:
        before = len(self._cache)
        if provider:
            self._cache = {k: v for k, v in self._cache.items() if not k.startswith(f"{provider}:")}
        else:
            self._cache.clear()
        return before - len(self._cache)

    def get_stats(self) -> Dict[str, Any]:
        total = self._hits + self._misses
        return {"entries": len(self._cache), "hits": self._hits, "misses": self._misses,
                "hit_rate": self._hits / total if total > 0 else 0.0,
                "max_entries": self._max_entries, "ttl": self._ttl}

    def clear(self) -> None:
        self._cache.clear()
        self._hits = 0
        self._misses = 0
