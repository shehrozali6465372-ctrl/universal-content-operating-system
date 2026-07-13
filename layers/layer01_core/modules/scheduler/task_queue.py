"""
Task Queue Module
Layer 1: Core System — Module 7

Priority-based task queue with states.
"""

from typing import Dict, Any, Optional, List
from enum import Enum
from datetime import datetime, timezone
from dataclasses import dataclass, field
import uuid


class TaskPriority(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    NORMAL = "NORMAL"
    LOW = "LOW"
    BACKGROUND = "BACKGROUND"


TASK_PRIORITY_ORDER = {
    TaskPriority.CRITICAL: 0,
    TaskPriority.HIGH: 1,
    TaskPriority.NORMAL: 2,
    TaskPriority.LOW: 3,
    TaskPriority.BACKGROUND: 4,
}


class TaskStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    WAITING = "WAITING"  # Waiting for dependencies


@dataclass
class Task:
    """Single task in the queue."""
    name: str
    job_type: str
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    params: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    timeout_seconds: int = 300
    max_retries: int = 3
    task_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    conditions: Optional[Dict] = None  # Decision-based conditions

    def __lt__(self, other: "Task") -> bool:
        return TASK_PRIORITY_ORDER[self.priority] < TASK_PRIORITY_ORDER[other.priority]


class TaskQueue:
    """Priority queue for tasks with dependency management."""

    def __init__(self):
        self._tasks: Dict[str, Task] = {}

    def add(self, task: Task) -> str:
        self._tasks[task.task_id] = task
        return task.task_id

    def get(self, task_id: str) -> Optional[Task]:
        return self._tasks.get(task_id)

    def next_task(self) -> Optional[Task]:
        """Get the highest priority task that's ready to run."""
        ready = [
            t for t in self._tasks.values()
            if t.status == TaskStatus.PENDING and self._dependencies_met(t)
        ]
        if not ready:
            return None
        ready.sort()
        return ready[0]

    def _dependencies_met(self, task: Task) -> bool:
        return all(
            self._tasks.get(dep_id, Task("", "")).status == TaskStatus.SUCCESS
            for dep_id in task.dependencies
        )

    def update_status(self, task_id: str, status: TaskStatus) -> None:
        if task_id in self._tasks:
            self._tasks[task_id].status = status

    def get_by_status(self, status: TaskStatus) -> List[Task]:
        return [t for t in self._tasks.values() if t.status == status]

    def get_by_name(self, name: str) -> Optional[Task]:
        for t in self._tasks.values():
            if t.name == name:
                return t
        return None

    def cancel(self, task_id: str) -> bool:
        if task_id in self._tasks:
            self._tasks[task_id].status = TaskStatus.CANCELLED
            return True
        return False

    def clear_completed(self) -> None:
        self._tasks = {
            tid: t for tid, t in self._tasks.items()
            if t.status not in (TaskStatus.SUCCESS, TaskStatus.FAILED, TaskStatus.CANCELLED)
        }

    @property
    def pending_count(self) -> int:
        return len(self.get_by_status(TaskStatus.PENDING))

    @property
    def total_count(self) -> int:
        return len(self._tasks)
