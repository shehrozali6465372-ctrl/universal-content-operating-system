"""GovernanceCache — cache governance check results."""
from __future__ import annotations
import time
from typing import Any, Dict, Optional

class GovernanceCache:
    def __init__(self, max_size: int = 200, ttl: int = 3600) -> None:
        self.max_size = max_size; self.ttl = ttl
        self._cache: Dict[str, Dict[str, Any]] = {}
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        e = self._cache.get(key)
        if e and (time.time() - e["ts"]) < self.ttl: return e["data"]
        return None
    def set(self, key: str, data: Dict[str, Any]) -> None:
        if len(self._cache) >= self.max_size:
            del self._cache[min(self._cache, key=lambda k: self._cache[k]["ts"])]
        self._cache[key] = {"data": data, "ts": time.time()}
    def clear(self) -> None: self._cache.clear()
    def stats(self) -> Dict[str, Any]: return {"size": len(self._cache)}
