"""ttl_manager.py — TTL management for Redis keys."""
from __future__ import annotations
import time
from typing import Any, Dict, Optional


class TTLManager:
    """Manages TTL for Redis keys."""

    def __init__(self) -> None:
        self._ttls: Dict[str, float] = {}

    def set(self, key: str, ttl_seconds: float) -> None:
        self._ttls[key] = time.time() + ttl_seconds

    def get_ttl(self, key: str) -> Optional[float]:
        expires = self._ttls.get(key)
        if expires is None:
            return None
        remaining = expires - time.time()
        return max(0.0, remaining)

    def is_expired(self, key: str) -> bool:
        ttl = self.get_ttl(key)
        return ttl is not None and ttl <= 0

    def delete(self, key: str) -> bool:
        return self._ttls.pop(key, None) is not None

    def cleanup_expired(self) -> int:
        expired = [k for k in list(self._ttls.keys()) if self.is_expired(k)]
        for k in expired:
            del self._ttls[k]
        return len(expired)

    def get_all(self) -> Dict[str, Optional[float]]:
        return {k: self.get_ttl(k) for k in self._ttls}

    def stats(self) -> Dict[str, Any]:
        return {"tracked_keys": len(self._ttls), "expired": self.cleanup_expired()}
