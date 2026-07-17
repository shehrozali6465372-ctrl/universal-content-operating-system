"""Priority Queue — Priority-based task queue."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from layers.layer10_monetization.modules.task_scheduler.task import Task


class PriorityQueue:
    """Priority queue supporting 5 priority levels."""

    def __init__(self, max_size: int = 10000) -> None:
        self._max_size = max_size
        self._queues: Dict[int, List[Task]] = {
            0: [], 1: [], 2: [], 3: [], 4: [],
        }
        self._task_map: Dict[str, Task] = {}

    @property
    def size(self) -> int:
        return sum(len(q) for q in self._queues.values())

    @property
    def is_empty(self) -> bool:
        return self.size == 0

    @property
    def is_full(self) -> bool:
        return self.size >= self._max_size

    def push(self, task: Task) -> bool:
        if self.is_full:
            return False
        if not task.validate():
            return False
        task.status = "queued"
        self._queues[task.priority].append(task)
        self._task_map[task.task_id] = task
        return True

    def pop(self) -> Optional[Task]:
        for priority in range(5):
            if self._queues[priority]:
                task = self._queues[priority].pop(0)
                self._task_map.pop(task.task_id, None)
                return task
        return None

    def peek(self) -> Optional[Task]:
        for priority in range(5):
            if self._queues[priority]:
                return self._queues[priority][0]
        return None

    def remove(self, task_id: str) -> Optional[Task]:
        task = self._task_map.pop(task_id, None)
        if task:
            self._queues[task.priority] = [
                t for t in self._queues[task.priority] if t.task_id != task_id
            ]
            return task
        return None

    def update_priority(self, task_id: str, new_priority: int) -> bool:
        task = self._task_map.get(task_id)
        if not task or task.status != "queued":
            return False
        self._queues[task.priority] = [
            t for t in self._queues[task.priority] if t.task_id != task_id
        ]
        task.priority = new_priority
        self._queues[new_priority].append(task)
        return True

    def get_by_layer(self, layer: str) -> List[Task]:
        results = []
        for q in self._queues.values():
            results.extend([t for t in q if t.layer == layer])
        return results

    def get_by_status(self, status: str) -> List[Task]:
        results = []
        for q in self._queues.values():
            results.extend([t for t in q if t.status == status])
        return results

    def get_all(self) -> List[Task]:
        results = []
        for priority in range(5):
            results.extend(self._queues[priority])
        return results

    def clear(self) -> None:
        for q in self._queues.values():
            q.clear()
        self._task_map.clear()

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total": self.size,
            "by_priority": {p: len(q) for p, q in self._queues.items()},
            "max_size": self._max_size,
        }
