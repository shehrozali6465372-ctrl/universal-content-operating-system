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

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("task name must be a non-empty string")
        if not isinstance(self.job_type, str) or not self.job_type.strip():
            raise ValueError("job_type must be a non-empty string")
        if not isinstance(self.task_id, str) or not self.task_id.strip():
            raise ValueError("task_id must be a non-empty string")
        if not isinstance(self.created_at, str):
            raise TypeError("created_at must be an ISO-8601 string")
        try:
            created = datetime.fromisoformat(self.created_at)
        except ValueError as exc:
            raise ValueError("created_at must be a valid ISO-8601 timestamp") from exc
        if created.tzinfo is None or created.utcoffset() is None:
            raise ValueError("created_at must include a timezone offset")
        if not isinstance(self.params, dict):
            raise TypeError("task params must be a dictionary")
        try:
            json.dumps(self.params)
        except (TypeError, ValueError) as exc:
            raise TypeError("task params must be JSON-serializable") from exc
        if self.conditions is not None:
            if not isinstance(self.conditions, dict):
                raise TypeError("task conditions must be a dictionary")
            try:
                json.dumps(self.conditions)
            except (TypeError, ValueError) as exc:
                raise TypeError("task conditions must be JSON-serializable") from exc
        if not isinstance(self.dependencies, list) or not all(
            isinstance(dep, str) and dep.strip() for dep in self.dependencies
        ):
            raise TypeError("task dependencies must be a list of non-empty strings")
        if (
            not isinstance(self.timeout_seconds, int)
            or isinstance(self.timeout_seconds, bool)
            or self.timeout_seconds < 1
        ):
            raise ValueError("timeout_seconds must be a positive integer")
        if (
            not isinstance(self.max_retries, int)
            or isinstance(self.max_retries, bool)
            or self.max_retries < 0
        ):
            raise ValueError("max_retries must be a non-negative integer")
        if self.not_before is not None:
            if not isinstance(self.not_before, str):
                raise TypeError("not_before must be an ISO-8601 string")
            try:
                parsed = datetime.fromisoformat(self.not_before)
            except ValueError as exc:
                raise ValueError("not_before must be a valid ISO-8601 timestamp") from exc
            if parsed.tzinfo is None or parsed.utcoffset() is None:
                raise ValueError("not_before must include a timezone offset")

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
            timeout_seconds=data.get("timeout_seconds", 300),
            max_retries=data.get("max_retries", 3),
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
                if (
                    existing.name == task.name
                    and existing.job_type == task.job_type
                    and existing.params == task.params
                    and existing.dependencies == task.dependencies
                    and existing.conditions == task.conditions
                    and existing.status in (
                        TaskStatus.PENDING, TaskStatus.WAITING, TaskStatus.RUNNING
                    )
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
            dep_id in self._tasks
            and self._tasks[dep_id].status == TaskStatus.SUCCESS
            for dep_id in task.dependencies
        )

    def update_status(self, task_id: str, status: TaskStatus) -> None:
        if not isinstance(status, TaskStatus):
            raise TypeError("status must be a TaskStatus")
        transitions = {
            TaskStatus.PENDING: {
                TaskStatus.RUNNING, TaskStatus.CANCELLED, TaskStatus.WAITING
            },
            TaskStatus.WAITING: {
                TaskStatus.PENDING, TaskStatus.CANCELLED
            },
            TaskStatus.RUNNING: {
                TaskStatus.SUCCESS, TaskStatus.FAILED, TaskStatus.PENDING, TaskStatus.WAITING
            },
            TaskStatus.SUCCESS: set(),
            TaskStatus.FAILED: set(),
            TaskStatus.CANCELLED: set(),
        }
        with self._lock:
            task = self._tasks.get(task_id)
            if task is None:
                raise KeyError(f"Unknown task: {task_id}")
            current = task.status
            if status == current:
                return
            if status not in transitions[current]:
                raise ValueError(f"Invalid task status transition: {current.value} -> {status.value}")
            task.status = status
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
        """Cancel a task only while it has not been claimed for execution."""
        with self._lock:
            task = self._tasks.get(task_id)
            if task is None or task.status not in (TaskStatus.PENDING, TaskStatus.WAITING):
                return False
            task.status = TaskStatus.CANCELLED
            self._save()
            return True

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
        try:
            data = json.loads(self._persist_path.read_text(encoding="utf-8"))
            if not isinstance(data, dict) or not isinstance(data.get("tasks", []), list):
                raise ValueError("task queue persistence must contain a tasks list")
            loaded = {}
            for item in data["tasks"]:
                if not isinstance(item, dict):
                    raise ValueError("invalid persisted task record")
                task = Task.from_dict(item)
                # A process cannot safely resume an in-flight handler after a crash.
                # Keep the task terminal so a caller must explicitly replay it.
                if task.status == TaskStatus.RUNNING:
                    task.status = TaskStatus.FAILED
                if task.task_id in loaded:
                    raise ValueError(f"duplicate persisted task id: {task.task_id}")
                loaded[task.task_id] = task
            with self._lock:
                self._tasks = loaded
        except (OSError, json.JSONDecodeError, TypeError, ValueError, KeyError) as exc:
            raise RuntimeError(f"Task queue persistence is unreadable: {self._persist_path}") from exc

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
