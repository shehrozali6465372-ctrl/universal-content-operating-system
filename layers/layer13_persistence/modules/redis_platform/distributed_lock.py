"""distributed_lock.py — Distributed locking with Redis."""
from __future__ import annotations
import time
from typing import Any, Dict, Optional


class DistributedLock:
    """A distributed lock."""
    __slots__ = ("lock_key", "owner", "acquired_at", "timeout", "metadata")

    def __init__(self, lock_key: str, owner: str, timeout: float = 30.0) -> None:
        self.lock_key = lock_key
        self.owner = owner
        self.acquired_at: float = time.time()
        self.timeout = timeout
        self.metadata: Dict[str, Any] = {}

    def is_expired(self) -> bool:
        return (time.time() - self.acquired_at) > self.timeout

    def to_dict(self) -> Dict[str, Any]:
        return {"key": self.lock_key, "owner": self.owner,
                "expired": self.is_expired()}


class DistributedLockManager:
    """Manages distributed locks via Redis."""

    def __init__(self) -> None:
        self._locks: Dict[str, DistributedLock] = {}

    def acquire(self, lock_key: str, owner: str, timeout: float = 30.0) -> Optional[DistributedLock]:
        existing = self._locks.get(lock_key)
        if existing and not existing.is_expired():
            return None
        lock = DistributedLock(lock_key, owner, timeout)
        self._locks[lock_key] = lock
        return lock

    def release(self, lock_key: str, owner: str) -> bool:
        lock = self._locks.get(lock_key)
        if lock and lock.owner == owner:
            del self._locks[lock_key]
            return True
        return False

    def is_locked(self, lock_key: str) -> bool:
        lock = self._locks.get(lock_key)
        return lock is not None and not lock.is_expired()

    def force_release(self, lock_key: str) -> bool:
        return self._locks.pop(lock_key, None) is not None

    def cleanup_expired(self) -> int:
        expired = [k for k, v in self._locks.items() if v.is_expired()]
        for k in expired:
            del self._locks[k]
        return len(expired)

    def get_lock(self, lock_key: str) -> Optional[DistributedLock]:
        return self._locks.get(lock_key)

    def stats(self) -> Dict[str, Any]:
        return {"active_locks": len(self._locks)}
