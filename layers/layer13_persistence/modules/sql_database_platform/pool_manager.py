"""pool_manager.py — Connection pool management."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional


class PoolEntry:
    """Single pool entry."""
    __slots__ = ("entry_id", "is_available", "in_use", "created_at", "last_used")
    _counter = 0

    def __init__(self) -> None:
        PoolEntry._counter += 1
        self.entry_id: int = PoolEntry._counter
        self.is_available: bool = True
        self.in_use: bool = False
        self.created_at: float = time.time()
        self.last_used: float = time.time()


class PoolManager:
    """Manages connection pools."""

    def __init__(self, pool_size: int = 20, max_overflow: int = 10) -> None:
        self._pool_size = pool_size
        self._max_overflow = max_overflow
        self._pool: List[PoolEntry] = []
        self._overflow: List[PoolEntry] = []
        self._acquired: int = 0
        self._released: int = 0

    def initialize(self) -> bool:
        self._pool = [PoolEntry() for _ in range(self._pool_size)]
        return True

    def acquire(self) -> Optional[PoolEntry]:
        for entry in self._pool:
            if entry.is_available and not entry.in_use:
                entry.in_use = True
                entry.is_available = False
                entry.last_used = time.time()
                self._acquired += 1
                return entry
        if len(self._overflow) < self._max_overflow:
            entry = PoolEntry()
            entry.in_use = True
            entry.is_available = False
            self._overflow.append(entry)
            self._acquired += 1
            return entry
        return None

    def release(self, entry: PoolEntry) -> bool:
        entry.in_use = False
        entry.is_available = True
        entry.last_used = time.time()
        self._released += 1
        if entry in self._overflow:
            self._overflow.remove(entry)
        return True

    def get_stats(self) -> Dict[str, Any]:
        in_use = sum(1 for e in self._pool if e.in_use)
        return {"pool_size": self._pool_size, "max_overflow": self._max_overflow,
                "available": sum(1 for e in self._pool if e.is_available and not e.in_use),
                "in_use": in_use, "overflow": len(self._overflow),
                "total_acquired": self._acquired, "total_released": self._released}

    def close_all(self) -> int:
        count = len(self._pool) + len(self._overflow)
        self._pool.clear()
        self._overflow.clear()
        return count
