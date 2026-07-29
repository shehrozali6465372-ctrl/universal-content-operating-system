"""Data models for Scheduler & Workflow Orchestrator."""
from __future__ import annotations
import time
import threading
import uuid
from enum import Enum
from typing import Any, Dict, List, Optional


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"
    PAUSED = "paused"
    QUEUED = "queued"


class WorkflowStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


class Priority(int, Enum):
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


class WorkflowStep:
    """A single step in a workflow."""
    __slots__ = ("step_id", "name", "module", "action", "depends_on",
                 "timeout", "retry_count", "max_retries", "status", "started_at",
                 "completed_at", "result", "error")

    def __init__(self, name: str, module: str, action: str,
                 depends_on: Optional[List[str]] = None,
                 timeout: float = 300.0, max_retries: int = 3) -> None:
        self.step_id: str = f"step_{uuid.uuid4().hex[:8]}"
        self.name: str = name
        self.module: str = module
        self.action: str = action
        self.depends_on: List[str] = depends_on or []
        self.timeout: float = timeout
        self.retry_count: int = 0
        self.max_retries: int = max_retries
        self.status: str = "pending"
        self.started_at: Optional[float] = None
        self.completed_at: Optional[float] = None
        self.result: Dict[str, Any] = {}
        self.error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {s: getattr(self, s) for s in self.__slots__}


class WorkflowDefinition:
    """Definition of a complete workflow."""
    __slots__ = ("workflow_id", "name", "description", "steps", "status",
                 "priority", "created_at", "updated_at", "tags", "metadata")

    def __init__(self, name: str, description: str = "",
                 steps: Optional[List[WorkflowStep]] = None,
                 priority: Priority = Priority.NORMAL,
                 tags: Optional[List[str]] = None) -> None:
        self.workflow_id: str = f"wf_{uuid.uuid4().hex[:8]}"
        self.name: str = name
        self.description: str = description
        self.steps: List[WorkflowStep] = steps or []
        self.status: WorkflowStatus = WorkflowStatus.DRAFT
        self.priority: Priority = priority
        self.created_at: float = time.time()
        self.updated_at: float = time.time()
        self.tags: List[str] = tags or []
        self.metadata: Dict[str, Any] = {}

    def add_step(self, step: WorkflowStep) -> None:
        self.steps.append(step)
        self.updated_at = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "workflow_id": self.workflow_id,
            "name": self.name,
            "description": self.description,
            "steps": [s.to_dict() for s in self.steps],
            "status": self.status.value,
            "priority": self.priority.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "tags": self.tags,
            "metadata": self.metadata,
        }


class ScheduledJob:
    """A scheduled job instance."""
    __slots__ = ("job_id", "workflow_id", "name", "priority", "status",
                 "scheduled_time", "started_time", "completed_time",
                 "retry_count", "max_retries", "result", "error",
                 "created_at", "metadata")

    def __init__(self, workflow_id: str, name: str = "",
                 priority: Priority = Priority.NORMAL,
                 scheduled_time: Optional[float] = None,
                 max_retries: int = 3) -> None:
        self.job_id: str = f"job_{uuid.uuid4().hex[:8]}"
        self.workflow_id: str = workflow_id
        self.name: str = name
        self.priority: Priority = priority
        self.status: JobStatus = JobStatus.PENDING
        self.scheduled_time: float = scheduled_time or time.time()
        self.started_time: Optional[float] = None
        self.completed_time: Optional[float] = None
        self.retry_count: int = 0
        self.max_retries: int = max_retries
        self.result: Dict[str, Any] = {}
        self.error: Optional[str] = None
        self.created_at: float = time.time()
        self.metadata: Dict[str, Any] = {}

    @property
    def is_due(self) -> bool:
        return time.time() >= self.scheduled_time

    @property
    def duration_ms(self) -> float:
        if self.started_time and self.completed_time:
            return (self.completed_time - self.started_time) * 1000
        return 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {s: getattr(self, s) for s in self.__slots__}


class QueueItem:
    """Item in the job queue."""
    __slots__ = ("item_id", "job", "priority", "enqueued_at", "status")

    def __init__(self, job: ScheduledJob, priority: Priority = Priority.NORMAL) -> None:
        self.item_id: str = f"qi_{uuid.uuid4().hex[:8]}"
        self.job: ScheduledJob = job
        self.priority: Priority = priority
        self.enqueued_at: float = time.time()
        self.status: str = "queued"


class WorkflowResult:
    """Result of a workflow execution."""
    __slots__ = ("workflow_id", "job_id", "status", "steps_results",
                 "started_at", "completed_at", "duration_ms", "error")

    def __init__(self, workflow_id: str, job_id: str) -> None:
        self.workflow_id: str = workflow_id
        self.job_id: str = job_id
        self.status: str = "unknown"
        self.steps_results: Dict[str, Dict[str, Any]] = {}
        self.started_at: float = time.time()
        self.completed_at: Optional[float] = None
        self.duration_ms: float = 0.0
        self.error: Optional[str] = None

    def complete(self, status: str = "completed") -> None:
        self.completed_at = time.time()
        self.duration_ms = (self.completed_at - self.started_at) * 1000
        self.status = status

    def to_dict(self) -> Dict[str, Any]:
        return {s: getattr(self, s) for s in self.__slots__}


class ExecutionLog:
    """Execution log entry."""
    __slots__ = ("log_id", "job_id", "workflow_id", "step_name", "module",
                 "action", "status", "duration_ms", "error", "timestamp")

    def __init__(self, job_id: str, workflow_id: str, step_name: str,
                 module: str, action: str, status: str = "pending") -> None:
        self.log_id: str = f"log_{uuid.uuid4().hex[:8]}"
        self.job_id: str = job_id
        self.workflow_id: str = workflow_id
        self.step_name: str = step_name
        self.module: str = module
        self.action: str = action
        self.status: str = status
        self.duration_ms: float = 0.0
        self.error: Optional[str] = None
        self.timestamp: float = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {s: getattr(self, s) for s in self.__slots__}


class EventRecord:
    """Event record for the event system."""
    __slots__ = ("event_id", "event_type", "source", "data", "timestamp")

    def __init__(self, event_type: str, source: str = "",
                 data: Optional[Dict[str, Any]] = None) -> None:
        self.event_id: str = f"evt_{uuid.uuid4().hex[:8]}"
        self.event_type: str = event_type
        self.source: str = source
        self.data: Dict[str, Any] = data or {}
        self.timestamp: float = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {s: getattr(self, s) for s in self.__slots__}


class Notification:
    """Notification record."""
    __slots__ = ("notification_id", "title", "message", "level",
                 "source", "job_id", "created_at", "read")

    def __init__(self, title: str, message: str, level: str = "info",
                 source: str = "", job_id: str = "") -> None:
        self.notification_id: str = f"notif_{uuid.uuid4().hex[:8]}"
        self.title: str = title
        self.message: str = message
        self.level: str = level
        self.source: str = source
        self.job_id: str = job_id
        self.created_at: float = time.time()
        self.read: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {s: getattr(self, s) for s in self.__slots__}


class ResourceMetrics:
    """Resource usage metrics."""
    __slots__ = ("cpu_percent", "memory_mb", "workers_active", "workers_idle",
                 "queue_size", "threads", "timestamp")

    def __init__(self, cpu_percent: float = 0.0, memory_mb: float = 0.0,
                 workers_active: int = 0, workers_idle: int = 0,
                 queue_size: int = 0, threads: int = 0) -> None:
        self.cpu_percent: float = cpu_percent
        self.memory_mb: float = memory_mb
        self.workers_active: int = workers_active
        self.workers_idle: int = workers_idle
        self.queue_size: int = queue_size
        self.threads: int = threads
        self.timestamp: float = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {s: getattr(self, s) for s in self.__slots__}


class WorkflowAnalytics:
    """Workflow analytics data."""
    __slots__ = ("total_jobs", "completed", "failed", "running", "pending",
                 "success_rate", "avg_duration_ms", "total_retries", "period")

    def __init__(self) -> None:
        self.total_jobs: int = 0
        self.completed: int = 0
        self.failed: int = 0
        self.running: int = 0
        self.pending: int = 0
        self.success_rate: float = 100.0
        self.avg_duration_ms: float = 0.0
        self.total_retries: int = 0
        self.period: str = "all_time"


class Dependency:
    """Workflow dependency definition."""
    __slots__ = ("dependency_id", "source_step", "target_step", "condition",
                 "optional", "timeout")

    def __init__(self, source_step: str, target_step: str,
                 condition: str = "completed", optional: bool = False,
                 timeout: float = 600.0) -> None:
        self.dependency_id: str = f"dep_{uuid.uuid4().hex[:8]}"
        self.source_step: str = source_step
        self.target_step: str = target_step
        self.condition: str = condition
        self.optional: bool = optional
        self.timeout: float = timeout
