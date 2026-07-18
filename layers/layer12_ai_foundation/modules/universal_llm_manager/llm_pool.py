"""LLMPool — Pool of available LLM connections."""
from __future__ import annotations
from typing import Any, Dict, List, Optional

class PoolEntry:
    __slots__ = ("provider", "model", "available", "active_count", "max_concurrent")
    def __init__(self, provider: str = "", model: str = "") -> None:
        self.provider = provider
        self.model = model
        self.available: bool = True
        self.active_count: int = 0
        self.max_concurrent: int = 5
    def is_available(self) -> bool:
        return self.available and self.active_count < self.max_concurrent

class LLMPool:
    def __init__(self) -> None:
        self._pool: List[PoolEntry] = []
    def register(self, provider: str, model: str, max_concurrent: int = 5) -> PoolEntry:
        entry = PoolEntry(provider, model)
        entry.max_concurrent = max_concurrent
        self._pool.append(entry)
        return entry
    def acquire(self, provider: str = "", model: str = "") -> Optional[PoolEntry]:
        for entry in self._pool:
            if entry.is_available() and (not provider or entry.provider == provider):
                entry.active_count += 1
                return entry
        return None
    def release(self, entry: PoolEntry) -> None:
        entry.active_count = max(0, entry.active_count - 1)
    def get_stats(self) -> Dict[str, Any]:
        return {"total": len(self._pool), "available": sum(1 for e in self._pool if e.is_available())}
