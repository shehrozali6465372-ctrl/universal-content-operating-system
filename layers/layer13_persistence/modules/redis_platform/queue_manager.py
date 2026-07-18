"""queue_manager.py — Redis queue (list-based)."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional


class QueueItem:
    """A queue item."""
    __slots__ = ("item_id", "data", "priority", "enqueued_at", "status")
    _counter = 0

    def __init__(self, data: str, priority: int = 0) -> None:
        QueueItem._counter += 1
        self.item_id: int = QueueItem._counter
        self.data = data
        self.priority = priority
        self.enqueued_at: float = time.time()
        self.status: str = "pending"

    def to_dict(self) -> Dict[str, Any]:
        return {"id": self.item_id, "data": self.data, "priority": self.priority,
                "status": self.status}


class QueueManager:
    """Redis-style queue implementation."""

    def __init__(self, max_size: int = 10000) -> None:
        self._queues: Dict[str, List[QueueItem]] = {}
        self._max_size = max_size

    def enqueue(self, queue_name: str, data: str, priority: int = 0) -> QueueItem:
        if queue_name not in self._queues:
            self._queues[queue_name] = []
        item = QueueItem(data, priority)
        self._queues[queue_name].append(item)
        self._queues[queue_name].sort(key=lambda x: x.priority, reverse=True)
        return item

    def dequeue(self, queue_name: str) -> Optional[QueueItem]:
        q = self._queues.get(queue_name, [])
        if q:
            item = q.pop(0)
            item.status = "processed"
            return item
        return None

    def peek(self, queue_name: str) -> Optional[QueueItem]:
        q = self._queues.get(queue_name, [])
        return q[0] if q else None

    def size(self, queue_name: str) -> int:
        return len(self._queues.get(queue_name, []))

    def clear(self, queue_name: str) -> int:
        q = self._queues.pop(queue_name, [])
        return len(q)

    def list_queues(self) -> List[str]:
        return list(self._queues.keys())

    def stats(self) -> Dict[str, Any]:
        sizes = {k: len(v) for k, v in self._queues.items()}
        return {"queues": len(self._queues), "sizes": sizes}
