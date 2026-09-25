"""Bounded async resource pool with identity-safe acquire/release."""
from __future__ import annotations

import asyncio
import time
import uuid
from typing import Any


class PooledResource:
    __slots__ = ("resource_id", "resource", "in_use", "acquired_at", "released_at",
                 "acquire_count", "metadata")

    def __init__(self, resource_id: str, resource: Any) -> None:
        self.resource_id = resource_id
        self.resource = resource
        self.in_use = False
        self.acquired_at = 0.0
        self.released_at = 0.0
        self.acquire_count = 0
        self.metadata: dict[str, Any] = {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "resource_id": self.resource_id, "in_use": self.in_use,
            "acquire_count": self.acquire_count,
        }


class ResourcePool:
    def __init__(self, name: str = "default") -> None:
        self.name = name
        self._resources: dict[str, PooledResource] = {}
        self._queue: asyncio.Queue[str] = asyncio.Queue()
        self._initialized = False

    def add_resource(self, resource: Any, resource_id: str | None = None) -> PooledResource:
        rid = resource_id or str(uuid.uuid4())
        if rid in self._resources:
            raise ValueError(f"resource_id already exists: {rid}")
        pooled = PooledResource(rid, resource)
        self._resources[rid] = pooled
        if self._initialized:
            self._queue.put_nowait(rid)
        return pooled

    def initialize(self) -> None:
        if self._initialized:
            return
        self._initialized = True
        for rid in self._resources:
            self._queue.put_nowait(rid)

    async def acquire(self, timeout: float = 10.0) -> Any | None:
        if timeout < 0:
            raise ValueError("timeout must be non-negative")
        self.initialize()
        try:
            rid = await asyncio.wait_for(self._queue.get(), timeout=timeout)
        except asyncio.TimeoutError:
            return None
        pooled = self._resources.get(rid)
        if pooled is None or pooled.in_use:
            return None
        pooled.in_use = True
        pooled.acquired_at = time.time()
        pooled.acquire_count += 1
        return pooled.resource

    async def release(self, resource: Any) -> bool:
        for pooled in self._resources.values():
            if pooled.resource is resource and pooled.in_use:
                pooled.in_use = False
                pooled.released_at = time.time()
                await self._queue.put(pooled.resource_id)
                return True
        return False

    def size(self) -> int:
        return len(self._resources)

    def available(self) -> int:
        return self._queue.qsize()

    def in_use(self) -> int:
        return sum(r.in_use for r in self._resources.values())

    def list_resources(self) -> list[dict[str, Any]]:
        return [r.to_dict() for r in self._resources.values()]

    def stats(self) -> dict[str, Any]:
        return {
            "name": self.name, "total": self.size(),
            "available": self.available(), "in_use": self.in_use(),
        }
