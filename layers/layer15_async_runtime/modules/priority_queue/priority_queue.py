"""PriorityQueue — priority-based async task queue."""
from __future__ import annotations
import asyncio
import heapq
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple
from enum import IntEnum


class Priority(IntEnum):
    CRITICAL = 0; HIGH = 1; NORMAL = 2; LOW = 3; BACKGROUND = 4


class PriorityItem:
    __slots__ = ("item_id", "priority", "payload", "enqueued_at", "metadata")

    def __init__(self, priority: Priority, payload: Any) -> None:
        self.item_id = str(uuid.uuid4())[:12]
        self.priority = priority
        self.payload = payload
        self.enqueued_at = time.time()
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {"item_id": self.item_id, "priority": self.priority.value,
                "enqueued_at": self.enqueued_at}


class PriorityQueue:
    def __init__(self) -> None:
        self._heap: List[Tuple[int, float, PriorityItem]] = []
        self._items: Dict[str, PriorityItem] = {}
        self._counter = 0

    def push(self, payload: Any, priority: Priority = Priority.NORMAL) -> PriorityItem:
        item = PriorityItem(priority, payload)
        self._items[item.item_id] = item
        heapq.heappush(self._heap, (priority.value, self._counter, item))
        self._counter += 1
        return item

    def pop(self) -> Optional[PriorityItem]:
        if self._heap:
            _, _, item = heapq.heappop(self._heap)
            self._items.pop(item.item_id, None)
            return item
        return None

    def peek(self) -> Optional[PriorityItem]:
        if self._heap:
            return self._heap[0][2]
        return None

    def remove(self, item_id: str) -> bool:
        if item_id in self._items:
            self._heap = [(p, c, i) for p, c, i in self._heap if i.item_id != item_id]
            heapq.heapify(self._heap)
            self._items.pop(item_id, None)
            return True
        return False

    def update_priority(self, item_id: str, new_priority: Priority) -> bool:
        item = self._items.get(item_id)
        if item:
            self.remove(item_id)
            item.priority = new_priority
            heapq.heappush(self._heap, (new_priority.value, self._counter, item))
            self._counter += 1
            return True
        return False

    def size(self) -> int:
        return len(self._heap)

    def is_empty(self) -> bool:
        return len(self._heap) == 0

    def list_items(self) -> List[Dict[str, Any]]:
        return [i.to_dict() for _, _, i in sorted(self._heap)]

    def stats(self) -> Dict[str, Any]:
        priorities = {}
        for _, _, item in self._heap:
            p = item.priority.name
            priorities[p] = priorities.get(p, 0) + 1
        return {"size": self.size(), "by_priority": priorities}
