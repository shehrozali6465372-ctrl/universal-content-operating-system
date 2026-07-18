"""lock_manager.py — Lock management."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional


class Lock:
    """A database lock."""
    __slots__ = ("lock_id", "resource", "lock_type", "holder", "acquired_at",
                 "timeout", "metadata")
    _counter = 0

    def __init__(self, resource: str, lock_type: str, holder: str,
                 timeout: float = 30.0) -> None:
        Lock._counter += 1
        self.lock_id: int = Lock._counter
        self.resource = resource
        self.lock_type = lock_type
        self.holder = holder
        self.acquired_at: float = time.time()
        self.timeout = timeout
        self.metadata: Dict[str, Any] = {}

    def is_expired(self) -> bool:
        return (time.time() - self.acquired_at) > self.timeout

    def to_dict(self) -> Dict[str, Any]:
        return {"lock_id": self.lock_id, "resource": self.resource,
                "type": self.lock_type, "holder": self.holder}


class LockManager:
    """Manages database locks."""

    def __init__(self) -> None:
        self._locks: Dict[str, Lock] = {}

    def acquire(self, resource: str, lock_type: str, holder: str,
                timeout: float = 30.0) -> Optional[Lock]:
        existing = self._locks.get(resource)
        if existing:
            if existing.is_expired():
                del self._locks[resource]
            elif lock_type == "exclusive" or existing.lock_type == "exclusive":
                return None
        lock = Lock(resource, lock_type, holder, timeout)
        self._locks[resource] = lock
        return lock

    def release(self, resource: str, holder: str) -> bool:
        lock = self._locks.get(resource)
        if lock and lock.holder == holder:
            del self._locks[resource]
            return True
        return False

    def is_locked(self, resource: str) -> bool:
        return resource in self._locks

    def get_lock(self, resource: str) -> Optional[Lock]:
        return self._locks.get(resource)

    def get_all_locks(self) -> List[Lock]:
        return list(self._locks.values())

    def clear_expired(self) -> int:
        expired = [k for k, v in self._locks.items() if v.is_expired()]
        for k in expired:
            del self._locks[k]
        return len(expired)

    def stats(self) -> Dict[str, Any]:
        types = {}
        for lock in self._locks.values():
            types[lock.lock_type] = types.get(lock.lock_type, 0) + 1
        return {"active_locks": len(self._locks), "by_type": types}
