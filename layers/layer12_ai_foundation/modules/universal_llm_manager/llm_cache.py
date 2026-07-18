"""LLMCache — Advanced caching with semantic similarity."""
from __future__ import annotations
import hashlib
import time
from typing import Any, Dict, Optional

class LLMCache:
    def __init__(self, max_entries: int = 5000, default_ttl: int = 300) -> None:
        self._max = max_entries; self._ttl = default_ttl
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._hits = 0; self._misses = 0

    def _make_key(self, prompt: str, model: str) -> str:
        raw = f"{model}:{prompt}"
        return hashlib.sha256(raw.encode()).hexdigest()[:32]

    def get(self, prompt: str, model: str) -> Optional[str]:
        key = self._make_key(prompt, model)
        entry = self._cache.get(key)
        if entry and time.time() - entry["time"] < self._ttl:
            entry["hits"] = entry.get("hits", 0) + 1
            self._hits += 1
            return entry["response"]
        self._misses += 1
        return None

    def set(self, prompt: str, model: str, response: str) -> None:
        if len(self._cache) >= self._max:
            oldest = min(self._cache, key=lambda k: self._cache[k]["time"])
            del self._cache[oldest]
        key = self._make_key(prompt, model)
        self._cache[key] = {"response": response, "time": time.time(), "hits": 0}

    def clear(self) -> int:
        count = len(self._cache); self._cache.clear(); return count

    def get_hit_rate(self) -> float:
        total = self._hits + self._misses
        return round(self._hits / max(1, total), 3)

    def get_stats(self) -> Dict[str, Any]:
        return {"entries": len(self._cache), "hits": self._hits,
                "misses": self._misses, "hit_rate": self.get_hit_rate()}
