"""Intelligence Cache — caches intelligence results for reuse."""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

class CachedResult:
    __slots__ = ("key", "data", "created_at", "hit_count")
    def __init__(self, key: str, data: Any):
        self.key = key
        self.data = data
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.hit_count = 0
    def to_dict(self) -> dict:
        return {"key": self.key, "hit_count": self.hit_count, "created_at": self.created_at}

class IntelligenceCache:
    def __init__(self, max_size: int = 500, ttl_seconds: int = 3600):
        self._cache: Dict[str, CachedResult] = {}
        self._max_size = max_size
        self._ttl = ttl_seconds
    def store(self, key: str, data: Any):
        if len(self._cache) >= self._max_size:
            oldest = min(self._cache.values(), key=lambda c: c.hit_count)
            del self._cache[oldest.key]
        self._cache[key] = CachedResult(key, data)
    def get(self, key: str) -> Optional[Any]:
        entry = self._cache.get(key)
        if entry:
            entry.hit_count += 1
            return entry.data
        return None
    def has(self, key: str) -> bool:
        return key in self._cache
    def remove(self, key: str) -> bool:
        return self._cache.pop(key, None) is not None
    def size(self) -> int:
        return len(self._cache)
    def hit_rate(self) -> float:
        total = sum(c.hit_count for c in self._cache.values())
        return round(total / max(len(self._cache), 1), 3)
    def clear(self):
        self._cache.clear()
    def keys(self) -> List[str]:
        return list(self._cache.keys())
