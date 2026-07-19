"""ResourcePool — manage limited resources with acquire/release pattern."""
from __future__ import annotations
import asyncio
import time
import uuid
from typing import Any, Dict, List, Optional


class PooledResource:
    __slots__ = ("resource_id", "resource", "in_use", "acquired_at", "released_at",
                 "acquire_count", "metadata")

    def __init__(self, resource_id: str, resource: Any) -> None:
        self.resource_id = resource_id
        self.resource = resource
        self.in_use = False
        self.acquired_at: float = 0.0
        self.released_at: float = 0.0
        self.acquire_count = 0
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {"resource_id": self.resource_id, "in_use": self.in_use,
                "acquire_count": self.acquire_count}


class ResourcePool:
    def __init__(self, name: str = "default") -> None:
        self.name = name
        self._resources: Dict[str, PooledResource] = {}
        self._semaphore: Optional[asyncio.Semaphore] = None
        self._queue: asyncio.Queue = asyncio.Queue()

    def add_resource(self, resource: Any, resource_id: Optional[str] = None) -> PooledResource:
        rid = resource_id or str(uuid.uuid4())[:12]
        pooled = PooledResource(rid, resource)
        self._resources[rid] = pooled
        return pooled

    def initialize(self) -> None:
        self._semaphore = asyncio.Semaphore(len(self._resources))
        for rid in self._resources:
            self._queue.put_nowait(rid)

    async def acquire(self, timeout: float = 10.0) -> Optional[Any]:
        if not self._semaphore:
            self.initialize()
        try:
            rid = await asyncio.wait_for(self._queue.get(), timeout=timeout)
            resource = self._resources.get(rid)
            if resource:
                resource.in_use = True
                resource.acquired_at = time.time()
                resource.acquire_count += 1
                return resource.resource
        except asyncio.TimeoutError:
            pass
        return None

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
        return sum(1 for r in self._resources.values() if r.in_use)

    def list_resources(self) -> List[Dict[str, Any]]:
        return [r.to_dict() for r in self._resources.values()]

    def stats(self) -> Dict[str, Any]:
        return {"name": self.name, "total": self.size(),
                "available": self.available(), "in_use": self.in_use()}
