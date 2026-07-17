"""Task model for the scheduler."""
from __future__ import annotations
import itertools
import time
from typing import Any, Dict, Optional

_TASK_COUNTER = itertools.count(1)

PRIORITY_CRITICAL = 0
PRIORITY_HIGH = 1
PRIORITY_NORMAL = 2
PRIORITY_LOW = 3
PRIORITY_BACKGROUND = 4

TASK_STATUSES = ("pending", "queued", "running", "completed", "failed", "cancelled", "paused")


class Task:
    """Represents a schedulable task."""

    __slots__ = ("task_id", "workflow_id", "layer", "module", "priority",
                 "status", "deadline", "max_retries", "retry_count", "timeout",
                 "metadata", "created_at", "started_at", "completed_at",
                 "duration_ms", "error", "result", "assigned_worker", "resource_cost")

    def __init__(self, layer: str = "", module: str = "", priority: int = PRIORITY_NORMAL) -> None:
        self.task_id: str = f"task_{next(_TASK_COUNTER)}"
        self.workflow_id: str = ""
        self.layer = layer
        self.module = module
        self.priority = priority
        self.status: str = "pending"
        self.deadline: Optional[float] = None
        self.max_retries: int = 3
        self.retry_count: int = 0
        self.timeout: float = 300.0
        self.metadata: Dict[str, Any] = {}
        self.created_at: float = time.time()
        self.started_at: float = 0.0
        self.completed_at: float = 0.0
        self.duration_ms: float = 0.0
        self.error: Optional[str] = None
        self.result: Any = None
        self.assigned_worker: Optional[str] = None
        self.resource_cost: Dict[str, float] = {}

    def validate(self) -> bool:
        if not self.layer:
            return False
        if self.priority < 0 or self.priority > 4:
            return False
        return True

    def clone(self) -> "Task":
        t = Task(self.layer, self.module, self.priority)
        t.task_id = self.task_id
        t.workflow_id = self.workflow_id
        t.max_retries = self.max_retries
        t.timeout = self.timeout
        t.metadata = dict(self.metadata)
        t.resource_cost = dict(self.resource_cost)
        return t

    def start(self, worker_id: str = "") -> None:
        self.status = "running"
        self.started_at = time.time()
        self.assigned_worker = worker_id

    def complete(self, result: Any = None) -> None:
        self.status = "completed"
        self.result = result
        self.completed_at = time.time()
        if self.started_at:
            self.duration_ms = (self.completed_at - self.started_at) * 1000

    def fail(self, error: str = "") -> None:
        self.status = "failed"
        self.error = error
        self.completed_at = time.time()
        if self.started_at:
            self.duration_ms = (self.completed_at - self.started_at) * 1000

    def cancel(self) -> None:
        self.status = "cancelled"
        self.completed_at = time.time()

    def pause(self) -> None:
        if self.status == "running":
            self.status = "paused"

    def resume(self) -> None:
        if self.status == "paused":
            self.status = "running"

    def can_retry(self) -> bool:
        return self.status == "failed" and self.retry_count < self.max_retries

    def retry(self) -> bool:
        if self.can_retry():
            self.retry_count += 1
            self.status = "pending"
            self.error = None
            self.started_at = 0.0
            self.completed_at = 0.0
            self.duration_ms = 0.0
            self.assigned_worker = None
            return True
        return False

    @property
    def is_terminal(self) -> bool:
        return self.status in ("completed", "failed", "cancelled")

    @property
    def estimated_duration(self) -> float:
        return self.resource_cost.get("estimated_seconds", 1.0)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "workflow_id": self.workflow_id,
            "layer": self.layer,
            "module": self.module,
            "priority": self.priority,
            "status": self.status,
            "retry_count": self.retry_count,
            "assigned_worker": self.assigned_worker,
            "duration_ms": round(self.duration_ms, 1),
            "error": self.error,
        }
