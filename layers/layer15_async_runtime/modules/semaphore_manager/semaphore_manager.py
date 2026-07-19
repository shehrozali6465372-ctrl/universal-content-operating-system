"""SemaphoreManager — manage named semaphores for concurrency control."""
from __future__ import annotations
import asyncio
import time
from typing import Any, Dict, List, Optional


class ManagedSemaphore:
    __slots__ = ("name", "semaphore", "max_permits", "acquired_count",
                 "released_count", "current_count", "created_at", "metadata")

    def __init__(self, name: str, max_permits: int) -> None:
        self.name = name
        self.semaphore = asyncio.Semaphore(max_permits)
        self.max_permits = max_permits
        self.acquired_count = 0
        self.released_count = 0
        self.current_count = 0
        self.created_at = time.time()
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "max_permits": self.max_permits,
                "acquired_count": self.acquired_count,
                "released_count": self.released_count}


class SemaphoreManager:
    def __init__(self) -> None:
        self._semaphores: Dict[str, ManagedSemaphore] = {}

    def create(self, name: str, max_permits: int) -> ManagedSemaphore:
        sem = ManagedSemaphore(name, max_permits)
        self._semaphores[name] = sem
        return sem

    def get(self, name: str) -> Optional[ManagedSemaphore]:
        return self._semaphores.get(name)

    def acquire_sync(self, name: str) -> bool:
        sem = self._semaphores.get(name)
        if sem:
            acquired = sem.semaphore.locked()
            if not acquired:
                sem.acquired_count += 1
                sem.current_count += 1
                return True
        return False

    def release_sync(self, name: str) -> bool:
        sem = self._semaphores.get(name)
        if sem and sem.current_count > 0:
            sem.current_count -= 1
            sem.released_count += 1
            return True
        return False

    def remove(self, name: str) -> bool:
        if name in self._semaphores:
            del self._semaphores[name]
            return True
        return False

    def list_semaphores(self) -> List[Dict[str, Any]]:
        return [s.to_dict() for s in self._semaphores.values()]

    def stats(self) -> Dict[str, Any]:
        total_permits = sum(s.max_permits for s in self._semaphores.values())
        total_acquired = sum(s.acquired_count for s in self._semaphores.values())
        return {"total_semaphores": len(self._semaphores),
                "total_permits": total_permits,
                "total_acquisitions": total_acquired}

    def count(self) -> int:
        return len(self._semaphores)
