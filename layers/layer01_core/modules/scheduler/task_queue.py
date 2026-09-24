"""
Task Queue Module
Layer 1: Core System — Module 7

Priority-based task queue with states.
"""

from typing import Dict, Any, Optional, List
from enum import Enum
from datetime import datetime, timezone
from pathlib import Path
import json
import os
import tempfile
from dataclasses import dataclass, field
import uuid
from threading import RLock


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
    not_before: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name, "job_type": self.job_type,
            "priority": self.priority.value, "status": self.status.value,
            "params": self.params, "dependencies": self.dependencies,
            "timeout_seconds": self.timeout_seconds, "max_retries": self.max_retries,
            "task_id": self.task_id, "created_at": self.created_at,
            "conditions": self.conditions, "not_before": self.not_before,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        return cls(
            name=data["name"], job_type=data["job_type"],
            priority=TaskPriority(data.get("priority", "NORMAL")),
            status=TaskStatus(data.get("status", "PENDING")),
            params=data.get("params", {}), dependencies=data.get("dependencies", []),
            timeout_seconds=int(data.get("timeout_seconds", 300)),
            max_retries=int(data.get("max_retries", 3)),
            task_id=data.get("task_id") or uuid.uuid4().hex[:12],
            created_at=data.get("created_at") or datetime.now(timezone.utc).isoformat(),
            conditions=data.get("conditions"), not_before=data.get("not_before"),
        )

    def __lt__(self, other: "Task") -> bool:
        return TASK_PRIORITY_ORDER[self.priority] < TASK_PRIORITY_ORDER[other.priority]


class TaskQueue:
    """Priority queue for tasks with dependency management."""

    def __init__(self, persist_path: Optional[str] = None):
        self._tasks: Dict[str, Task] = {}
        self._lock = RLock()
        self._persist_path = Path(persist_path) if persist_path else None
        self._load()

    def add(self, task: Task) -> str:
        with self._lock:
            # Task name + job type is the idempotency key while an equivalent
            # task is active. Callers can use a unique name to enqueue a new run.
            for existing in self._tasks.values():
                if existing.name == task.name and existing.job_type == task.job_type and existing.status in (
                    TaskStatus.PENDING, TaskStatus.WAITING, TaskStatus.RUNNING
                ):
                    return existing.task_id
            self._tasks[task.task_id] = task
            self._save()
            return task.task_id

    def get(self, task_id: str) -> Optional[Task]:
        with self._lock:
            return self._tasks.get(task_id)

    def next_task(self) -> Optional[Task]:
        """Atomically claim and return the highest-priority ready task."""
        with self._lock:
            now = datetime.now(timezone.utc)
            ready = []
            for t in self._tasks.values():
                if t.status != TaskStatus.PENDING or not self._dependencies_met(t):
                    continue
                if t.not_before:
                    try:
                        if now < datetime.fromisoformat(t.not_before):
                            continue
                    except (TypeError, ValueError):
                        continue
                ready.append(t)
            if not ready:
                return None
            ready.sort()
            task = ready[0]
            task.status = TaskStatus.RUNNING
            self._save()
            return task

    def claim(self, task_id: str) -> bool:
        """Atomically claim a pending, dependency-ready, due task."""
        with self._lock:
            task = self._tasks.get(task_id)
            if task is None or task.status != TaskStatus.PENDING:
                return False
            if not self._dependencies_met(task):
                return False
            if task.not_before:
                try:
                    if datetime.now(timezone.utc) < datetime.fromisoformat(task.not_before):
                        return False
                except (TypeError, ValueError):
                    return False
            task.status = TaskStatus.RUNNING
            self._save()
            return True

    def _dependencies_met(self, task: Task) -> bool:
        return all(
            self._tasks.get(dep_id, Task("", "")).status == TaskStatus.SUCCESS
            for dep_id in task.dependencies
        )

    def update_status(self, task_id: str, status: TaskStatus) -> None:
        with self._lock:
            if task_id in self._tasks:
                self._tasks[task_id].status = status
                self._save()

    def get_by_status(self, status: TaskStatus) -> List[Task]:
        with self._lock:
            return [t for t in self._tasks.values() if t.status == status]

    def get_by_name(self, name: str) -> Optional[Task]:
        with self._lock:
            for t in self._tasks.values():
                if t.name == name:
                    return t
            return None

    def cancel(self, task_id: str) -> bool:
        with self._lock:
            if task_id in self._tasks:
                self._tasks[task_id].status = TaskStatus.CANCELLED
                self._save()
                return True
        return False

    def clear_completed(self) -> None:
        with self._lock:
            self._tasks = {
                tid: t for tid, t in self._tasks.items()
                if t.status not in (TaskStatus.SUCCESS, TaskStatus.FAILED, TaskStatus.CANCELLED)
            }
            self._save()

    def _load(self) -> None:
        if not self._persist_path or not self._persist_path.exists():
            return
        data = json.loads(self._persist_path.read_text(encoding="utf-8"))
        for item in data.get("tasks", []):
            task = Task.from_dict(item)
            # A process cannot safely resume an in-flight handler after a crash.
            if task.status == TaskStatus.RUNNING:
                task.status = TaskStatus.PENDING
            self._tasks[task.task_id] = task

    def _save(self) -> None:
        if not self._persist_path:
            return
        self._persist_path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_name = tempfile.mkstemp(dir=str(self._persist_path.parent), prefix=".queue.", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump({"tasks": [t.to_dict() for t in self._tasks.values()]}, f, indent=2, default=str)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_name, self._persist_path)
        except Exception:
            try:
                os.unlink(tmp_name)
            except OSError:
                pass
            raise

    @property
    def pending_count(self) -> int:
        return len(self.get_by_status(TaskStatus.PENDING))

    @property
    def total_count(self) -> int:
        with self._lock:
            return len(self._tasks)
