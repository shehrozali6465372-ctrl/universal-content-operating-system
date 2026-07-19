"""AICache — cache orchestrator results."""
from __future__ import annotations
import time
from typing import Any, Dict, Optional

class AICache:
    def __init__(self, max_size: int = 200, ttl: int = 3600) -> None:
        self.max_size = max_size; self.ttl = ttl
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._hits = 0; self._misses = 0
    def get(self, key: str) -> Optional[Any]:
        e = self._cache.get(key)
        if e and (time.time() - e["ts"]) < self.ttl: self._hits += 1; return e["data"]
        self._misses += 1; return None
    def set(self, key: str, data: Any) -> None:
        if len(self._cache) >= self.max_size:
            del self._cache[min(self._cache, key=lambda k: self._cache[k]["ts"])]
        self._cache[key] = {"data": data, "ts": time.time()}
    def clear(self) -> None: self._cache.clear(); self._hits = 0; self._misses = 0
    def stats(self) -> Dict[str, Any]:
        total = self._hits + self._misses
        return {"size": len(self._cache), "hits": self._hits, "misses": self._misses,
                "hit_rate": round(self._hits / total, 4) if total else 0}
