"""Named semaphore manager with real async permit accounting."""
from __future__ import annotations

import asyncio
import time
from typing import Any


class ManagedSemaphore:
    __slots__ = ("name", "semaphore", "max_permits", "acquired_count",
                 "released_count", "current_count", "created_at", "metadata")

    def __init__(self, name: str, max_permits: int) -> None:
        if max_permits <= 0:
            raise ValueError("max_permits must be positive")
        self.name = name
        self.semaphore = asyncio.Semaphore(max_permits)
        self.max_permits = max_permits
        self.acquired_count = 0
        self.released_count = 0
        self.current_count = 0
        self.created_at = time.time()
        self.metadata: dict[str, Any] = {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name, "max_permits": self.max_permits,
            "acquired_count": self.acquired_count,
            "released_count": self.released_count,
            "current_count": self.current_count,
        }


class SemaphoreManager:
    def __init__(self) -> None:
        self._semaphores: dict[str, ManagedSemaphore] = {}

    def create(self, name: str, max_permits: int) -> ManagedSemaphore:
        if name in self._semaphores:
            raise ValueError(f"semaphore already exists: {name}")
        sem = ManagedSemaphore(name, max_permits)
        self._semaphores[name] = sem
        return sem

    def get(self, name: str) -> ManagedSemaphore | None:
        return self._semaphores.get(name)

    async def acquire(self, name: str, timeout: float | None = None) -> bool:
        sem = self._semaphores.get(name)
        if sem is None:
            return False
        try:
            if timeout is None:
                await sem.semaphore.acquire()
            else:
                if timeout < 0:
                    raise ValueError("timeout must be non-negative")
                await asyncio.wait_for(sem.semaphore.acquire(), timeout)
        except asyncio.TimeoutError:
            return False
        sem.acquired_count += 1
        sem.current_count += 1
        return True

    def release(self, name: str) -> bool:
        sem = self._semaphores.get(name)
        if sem is None or sem.current_count <= 0:
            return False
        sem.semaphore.release()
        sem.current_count -= 1
        sem.released_count += 1
        return True

    async def acquire_sync(self, name: str) -> bool:
        return await self.acquire(name)

    def release_sync(self, name: str) -> bool:
        return self.release(name)

    def remove(self, name: str) -> bool:
        sem = self._semaphores.get(name)
        if sem is None or sem.current_count:
            return False
        del self._semaphores[name]
        return True

    def list_semaphores(self) -> list[dict[str, Any]]:
        return [s.to_dict() for s in self._semaphores.values()]

    def stats(self) -> dict[str, Any]:
        return {
            "total_semaphores": len(self._semaphores),
            "total_permits": sum(s.max_permits for s in self._semaphores.values()),
            "total_acquisitions": sum(s.acquired_count for s in self._semaphores.values()),
            "current_acquisitions": sum(s.current_count for s in self._semaphores.values()),
        }

    def count(self) -> int:
        return len(self._semaphores)
