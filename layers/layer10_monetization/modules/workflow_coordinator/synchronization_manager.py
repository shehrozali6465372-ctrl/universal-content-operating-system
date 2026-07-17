"""Synchronization Manager — Handle parallel execution synchronization."""
from __future__ import annotations
import itertools
import time
from typing import Any, Dict, List, Optional

_SYNC_COUNTER = itertools.count(1)


class SyncBarrier:
    """Barrier synchronization for parallel stages."""

    __slots__ = ("barrier_id", "expected_count", "arrived", "released")

    def __init__(self, expected_count: int = 0) -> None:
        self.barrier_id: str = f"barrier_{next(_SYNC_COUNTER)}"
        self.expected_count = expected_count
        self.arrived: int = 0
        self.released: bool = False

    def arrive(self) -> bool:
        self.arrived += 1
        if self.arrived >= self.expected_count:
            self.released = True
            return True
        return False

    def is_released(self) -> bool:
        return self.released

    def to_dict(self) -> Dict[str, Any]:
        return {
            "barrier_id": self.barrier_id,
            "expected": self.expected_count,
            "arrived": self.arrived,
            "released": self.released,
        }


class SyncLock:
    """Simple named lock for resource synchronization."""

    __slots__ = ("name", "owner", "acquired_at")

    def __init__(self, name: str = "") -> None:
        self.name = name
        self.owner: Optional[str] = None
        self.acquired_at: float = 0.0

    def acquire(self, owner: str = "default") -> bool:
        if self.owner is None:
            self.owner = owner
            self.acquired_at = time.time()
            return True
        return False

    def release(self) -> bool:
        if self.owner is not None:
            self.owner = None
            return True
        return False

    @property
    def is_locked(self) -> bool:
        return self.owner is not None


class SynchronizationManager:
    """Manage synchronization across parallel workflow stages."""

    def __init__(self) -> None:
        self._barriers: Dict[str, SyncBarrier] = {}
        self._locks: Dict[str, SyncLock] = {}
        self._shared_state: Dict[str, Any] = {}

    def create_barrier(self, name: str, expected_count: int) -> SyncBarrier:
        barrier = SyncBarrier(expected_count)
        self._barriers[name] = barrier
        return barrier

    def arrive_at_barrier(self, name: str) -> bool:
        barrier = self._barriers.get(name)
        if barrier:
            return barrier.arrive()
        return False

    def is_barrier_released(self, name: str) -> bool:
        barrier = self._barriers.get(name)
        return barrier.is_released() if barrier else False

    def acquire_lock(self, name: str, owner: str = "default") -> bool:
        if name not in self._locks:
            self._locks[name] = SyncLock(name)
        return self._locks[name].acquire(owner)

    def release_lock(self, name: str) -> bool:
        lock = self._locks.get(name)
        return lock.release() if lock else False

    def is_locked(self, name: str) -> bool:
        lock = self._locks.get(name)
        return lock.is_locked if lock else False

    def set_shared(self, key: str, value: Any) -> None:
        self._shared_state[key] = value

    def get_shared(self, key: str, default: Any = None) -> Any:
        return self._shared_state.get(key, default)

    def clear_shared(self) -> None:
        self._shared_state.clear()

    def join_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        merged: Dict[str, Any] = {}
        for r in results:
            merged.update(r)
        return merged

    def get_diagnostics(self) -> Dict[str, Any]:
        return {
            "barriers": len(self._barriers),
            "locks": len(self._locks),
            "shared_keys": list(self._shared_state.keys()),
            "locked_count": sum(1 for l in self._locks.values() if l.is_locked),
        }
