"""TaskQueue — FIFO task queue with async put/get operations."""
from __future__ import annotations
import asyncio
import time
import uuid
from typing import Any, Callable, Dict, List, Optional
from enum import Enum


class QueueState(str, Enum):
    ACTIVE = "active"; PAUSED = "paused"; STOPPED = "stopped"


class QueueItem:
    __slots__ = ("item_id", "payload", "handler", "status", "enqueued_at",
                 "dequeued_at", "completed_at", "result", "error", "metadata")

    def __init__(self, payload: Any, handler: Optional[Callable] = None) -> None:
        self.item_id = str(uuid.uuid4())[:12]
        self.payload = payload
        self.handler = handler
        self.status = "pending"
        self.enqueued_at = time.time()
        self.dequeued_at: float = 0.0
        self.completed_at: float = 0.0
        self.result: Any = None
        self.error: Optional[str] = None
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {"item_id": self.item_id, "status": self.status,
                "enqueued_at": self.enqueued_at}


class TaskQueue:
    def __init__(self, max_size: int = 1000) -> None:
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=max_size)
        self._max_size = max_size
        self._state = QueueState.ACTIVE
        self._items: Dict[str, QueueItem] = {}
        self._processed = 0
        self._dropped = 0

    async def enqueue(self, payload: Any, handler: Optional[Callable] = None) -> QueueItem:
        item = QueueItem(payload, handler)
        self._items[item.item_id] = item
        try:
            self._queue.put_nowait(item)
            self._processed += 1
        except asyncio.QueueFull:
            item.status = "dropped"
            self._dropped += 1
        return item

    async def dequeue(self, timeout: float = 1.0) -> Optional[QueueItem]:
        try:
            item = await asyncio.wait_for(self._queue.get(), timeout=timeout)
            item.status = "processing"
            item.dequeued_at = time.time()
            return item
        except asyncio.TimeoutError:
            return None

    def complete(self, item_id: str, result: Any = None) -> bool:
        item = self._items.get(item_id)
        if item:
            item.status = "completed"
            item.result = result
            item.completed_at = time.time()
            return True
        return False

    def fail(self, item_id: str, error: str) -> bool:
        item = self._items.get(item_id)
        if item:
            item.status = "failed"
            item.error = error
            item.completed_at = time.time()
            return True
        return False

    def pause(self) -> None:
        self._state = QueueState.PAUSED

    def resume(self) -> None:
        self._state = QueueState.ACTIVE

    def stop(self) -> None:
        self._state = QueueState.STOPPED

    def size(self) -> int:
        return self._queue.qsize()

    def stats(self) -> Dict[str, Any]:
        return {"state": self._state.value, "size": self._queue.qsize(),
                "max_size": self._max_size, "total_enqueued": len(self._items),
                "processed": self._processed, "dropped": self._dropped}

    def get_item(self, item_id: str) -> Optional[QueueItem]:
        return self._items.get(item_id)
