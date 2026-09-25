"""Bounded async task queue with explicit lifecycle semantics."""
from __future__ import annotations

import asyncio
import time
import uuid
from enum import Enum
from typing import Any, Callable


class QueueState(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    STOPPED = "stopped"


class QueueItem:
    __slots__ = ("item_id", "payload", "handler", "status", "enqueued_at",
                 "dequeued_at", "completed_at", "result", "error", "metadata")

    def __init__(self, payload: Any, handler: Callable[..., Any] | None = None) -> None:
        self.item_id = str(uuid.uuid4())
        self.payload = payload
        self.handler = handler
        self.status = "pending"
        self.enqueued_at = time.time()
        self.dequeued_at = 0.0
        self.completed_at = 0.0
        self.result: Any = None
        self.error: str | None = None
        self.metadata: dict[str, Any] = {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "item_id": self.item_id, "status": self.status,
            "enqueued_at": self.enqueued_at, "dequeued_at": self.dequeued_at,
            "completed_at": self.completed_at, "error": self.error,
        }


class TaskQueue:
    def __init__(self, max_size: int = 1000) -> None:
        if max_size <= 0:
            raise ValueError("max_size must be positive")
        self._queue: asyncio.Queue[QueueItem] = asyncio.Queue(maxsize=max_size)
        self._max_size = max_size
        self._state = QueueState.ACTIVE
        self._items: dict[str, QueueItem] = {}
        self._enqueued = 0
        self._completed = 0
        self._dropped = 0

    async def enqueue(self, payload: Any, handler: Callable[..., Any] | None = None) -> QueueItem:
        item = QueueItem(payload, handler)
        if self._state != QueueState.ACTIVE:
            item.status = "rejected"
            self._items[item.item_id] = item
            self._dropped += 1
            return item
        self._items[item.item_id] = item
        try:
            self._queue.put_nowait(item)
        except asyncio.QueueFull:
            item.status = "dropped"
            self._dropped += 1
        else:
            self._enqueued += 1
        return item

    async def dequeue(self, timeout: float = 1.0) -> QueueItem | None:
        if timeout < 0:
            raise ValueError("timeout must be non-negative")
        if self._state == QueueState.STOPPED:
            return None
        while self._state == QueueState.PAUSED:
            await asyncio.sleep(min(timeout, 0.05))
        try:
            item = await asyncio.wait_for(self._queue.get(), timeout=timeout)
        except asyncio.TimeoutError:
            return None
        item.status = "processing"
        item.dequeued_at = time.time()
        return item

    def complete(self, item_id: str, result: Any = None) -> bool:
        item = self._items.get(item_id)
        if item is None or item.status != "processing":
            return False
        item.status = "completed"
        item.result = result
        item.completed_at = time.time()
        self._completed += 1
        self._queue.task_done()
        return True

    def fail(self, item_id: str, error: str) -> bool:
        item = self._items.get(item_id)
        if item is None or item.status != "processing":
            return False
        item.status = "failed"
        item.error = error
        item.completed_at = time.time()
        self._queue.task_done()
        return True

    def pause(self) -> None:
        if self._state == QueueState.ACTIVE:
            self._state = QueueState.PAUSED

    def resume(self) -> None:
        if self._state != QueueState.STOPPED:
            self._state = QueueState.ACTIVE

    def stop(self) -> None:
        self._state = QueueState.STOPPED

    def size(self) -> int:
        return self._queue.qsize()

    def stats(self) -> dict[str, Any]:
        return {
            "state": self._state.value, "size": self._queue.qsize(),
            "max_size": self._max_size, "total_enqueued": self._enqueued,
            "completed": self._completed, "dropped": self._dropped,
        }

    def get_item(self, item_id: str) -> QueueItem | None:
        return self._items.get(item_id)
