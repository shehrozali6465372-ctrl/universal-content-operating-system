"""Data models for Automation Engine."""
from __future__ import annotations
import time
import uuid
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class AutomationStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"


class TriggerType(str, Enum):
    TIME = "time"
    EVENT = "event"
    TRAFFIC = "traffic"
    REVENUE = "revenue"
    KEYWORD = "keyword"
    MANUAL = "manual"
    API = "api"
    CRON = "cron"


class Trigger:
    """A trigger that starts automation."""
    __slots__ = ("trigger_id", "name", "trigger_type", "config", "enabled",
                 "last_fired", "fire_count", "cooldown_seconds")

    def __init__(self, name: str, trigger_type: TriggerType,
                 config: Optional[Dict[str, Any]] = None,
                 cooldown_seconds: float = 300.0) -> None:
        self.trigger_id: str = f"trg_{uuid.uuid4().hex[:8]}"
        self.name: str = name
        self.trigger_type: TriggerType = trigger_type
        self.config: Dict[str, Any] = config or {}
        self.enabled: bool = True
        self.last_fired: Optional[float] = None
        self.fire_count: int = 0
        self.cooldown_seconds: float = cooldown_seconds

    @property
    def can_fire(self) -> bool:
        if not self.enabled:
            return False
        if self.last_fired is None:
            return True
        return (time.time() - self.last_fired) >= self.cooldown_seconds

    def fire(self) -> None:
        self.last_fired = time.time()
        self.fire_count += 1

    def to_dict(self) -> Dict[str, Any]:
        return {s: getattr(self, s) for s in self.__slots__}


class RuleAction:
    """Action to execute when a rule condition is met."""
    __slots__ = ("action_id", "action_type", "params", "target_module")

    def __init__(self, action_type: str, params: Optional[Dict[str, Any]] = None,
                 target_module: str = "") -> None:
        self.action_id: str = f"act_{uuid.uuid4().hex[:8]}"
        self.action_type: str = action_type
        self.params: Dict[str, Any] = params or {}
        self.target_module: str = target_module


class Rule:
    """An automation rule with condition and action."""
    __slots__ = ("rule_id", "name", "condition_expr", "actions", "enabled",
                 "priority", "trigger_count", "last_triggered", "metadata")

    def __init__(self, name: str, condition_expr: str,
                 actions: Optional[List[RuleAction]] = None,
                 priority: int = 100, metadata: Optional[Dict] = None) -> None:
        self.rule_id: str = f"rule_{uuid.uuid4().hex[:8]}"
        self.name: str = name
        self.condition_expr: str = condition_expr
        self.actions: List[RuleAction] = actions or []
        self.enabled: bool = True
        self.priority: int = priority
        self.trigger_count: int = 0
        self.last_triggered: Optional[float] = None
        self.metadata: Dict[str, Any] = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        return {s: getattr(self, s) for s in self.__slots__}


class PipelineTask:
    """A task in the automation pipeline."""
    __slots__ = ("task_id", "name", "module", "action", "order", "depends_on",
                 "timeout", "status", "result", "error", "started_at", "completed_at")

    def __init__(self, name: str, module: str, action: str, order: int = 0,
                 depends_on: Optional[List[str]] = None, timeout: float = 300.0) -> None:
        self.task_id: str = f"pt_{uuid.uuid4().hex[:8]}"
        self.name: str = name
        self.module: str = module
        self.action: str = action
        self.order: int = order
        self.depends_on: List[str] = depends_on or []
        self.timeout: float = timeout
        self.status: str = "pending"
        self.result: Dict[str, Any] = {}
        self.error: Optional[str] = None
        self.started_at: Optional[float] = None
        self.completed_at: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {s: getattr(self, s) for s in self.__slots__}


class Worker:
    """A background worker instance."""
    __slots__ = ("worker_id", "name", "status", "task", "started_at",
                 "completed_tasks", "failed_tasks", "is_busy")

    def __init__(self, name: str = "") -> None:
        self.worker_id: str = f"wrk_{uuid.uuid4().hex[:8]}"
        self.name: str = name or f"worker-{self.worker_id[-6:]}"
        self.status: str = "idle"
        self.task: Optional[str] = None
        self.started_at: Optional[float] = None
        self.completed_tasks: int = 0
        self.failed_tasks: int = 0
        self.is_busy: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {s: getattr(self, s) for s in self.__slots__}


class CronSchedule:
    """Cron-based schedule definition."""
    __slots__ = ("schedule_id", "name", "cron_expr", "workflow_id",
                 "enabled", "last_run", "next_run", "run_count")

    def __init__(self, name: str, cron_expr: str, workflow_id: str = "") -> None:
        self.schedule_id: str = f"cron_{uuid.uuid4().hex[:8]}"
        self.name: str = name
        self.cron_expr: str = cron_expr
        self.workflow_id: str = workflow_id
        self.enabled: bool = True
        self.last_run: Optional[float] = None
        self.next_run: float = time.time()
        self.run_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {s: getattr(self, s) for s in self.__slots__}


class RetryPolicy:
    """Smart retry policy configuration."""
    __slots__ = ("policy_id", "name", "max_retries", "base_delay",
                 "max_delay", "backoff_factor", "retry_on_errors")

    def __init__(self, name: str = "default", max_retries: int = 3,
                 base_delay: float = 5.0, max_delay: float = 300.0,
                 backoff_factor: float = 2.0,
                 retry_on_errors: Optional[List[str]] = None) -> None:
        self.policy_id: str = f"rp_{uuid.uuid4().hex[:8]}"
        self.name: str = name
        self.max_retries: int = max_retries
        self.base_delay: float = base_delay
        self.max_delay: float = max_delay
        self.backoff_factor: float = backoff_factor
        self.retry_on_errors: List[str] = retry_on_errors or []


class ScalingPolicy:
    """Auto-scaling policy."""
    __slots__ = ("policy_id", "name", "min_workers", "max_workers",
                 "cpu_threshold", "queue_threshold", "scale_up_by",
                 "scale_down_by", "cooldown")

    def __init__(self, name: str = "default", min_workers: int = 2,
                 max_workers: int = 20, cpu_threshold: float = 70.0,
                 queue_threshold: int = 50, scale_up_by: int = 2,
                 scale_down_by: int = 1, cooldown: float = 60.0) -> None:
        self.policy_id: str = f"sp_{uuid.uuid4().hex[:8]}"
        self.name: str = name
        self.min_workers: int = min_workers
        self.max_workers: int = max_workers
        self.cpu_threshold: float = cpu_threshold
        self.queue_threshold: int = queue_threshold
        self.scale_up_by: int = scale_up_by
        self.scale_down_by: int = scale_down_by
        self.cooldown: float = cooldown


class SafetyPolicy:
    """Safety policy to prevent abuse."""
    __slots__ = ("policy_id", "name", "max_daily_executions",
                 "max_concurrent", "min_interval_seconds",
                 "blocked_hours", "rate_limit_per_minute")

    def __init__(self, name: str = "default", max_daily_executions: int = 1000,
                 max_concurrent: int = 10, min_interval_seconds: float = 10.0,
                 blocked_hours: Optional[List[int]] = None,
                 rate_limit_per_minute: int = 60) -> None:
        self.policy_id: str = f"sf_{uuid.uuid4().hex[:8]}"
        self.name: str = name
        self.max_daily_executions: int = max_daily_executions
        self.max_concurrent: int = max_concurrent
        self.min_interval_seconds: float = min_interval_seconds
        self.blocked_hours: List[int] = blocked_hours or []
        self.rate_limit_per_minute: int = rate_limit_per_minute


class AutomationConfig:
    """Full automation engine configuration."""
    __slots__ = ("config_id", "triggers", "rules", "pipeline_tasks",
                 "workers", "cron_schedules", "retry_policy",
                 "scaling_policy", "safety_policy", "settings")

    def __init__(self) -> None:
        self.config_id: str = f"cfg_{uuid.uuid4().hex[:8]}"
        self.triggers: List[Trigger] = []
        self.rules: List[Rule] = []
        self.pipeline_tasks: List[PipelineTask] = []
        self.workers: List[Worker] = []
        self.cron_schedules: List[CronSchedule] = []
        self.retry_policy: RetryPolicy = RetryPolicy()
        self.scaling_policy: ScalingPolicy = ScalingPolicy()
        self.safety_policy: SafetyPolicy = SafetyPolicy()
        self.settings: Dict[str, Any] = {}


class AutomationResult:
    """Result of an automation execution."""
    __slots__ = ("result_id", "workflow_id", "trigger", "status",
                 "tasks_completed", "tasks_failed", "duration_ms",
                 "started_at", "completed_at", "error")

    def __init__(self, workflow_id: str = "", trigger: str = "") -> None:
        self.result_id: str = f"ar_{uuid.uuid4().hex[:8]}"
        self.workflow_id: str = workflow_id
        self.trigger: str = trigger
        self.status: str = "running"
        self.tasks_completed: int = 0
        self.tasks_failed: int = 0
        self.duration_ms: float = 0.0
        self.started_at: float = time.time()
        self.completed_at: Optional[float] = None
        self.error: Optional[str] = None

    def complete(self, status: str = "completed") -> None:
        self.completed_at = time.time()
        self.duration_ms = (self.completed_at - self.started_at) * 1000
        self.status = status

    def to_dict(self) -> Dict[str, Any]:
        return {s: getattr(self, s) for s in self.__slots__}


class ExecutionRecord:
    """Record of a single automation execution."""
    __slots__ = ("record_id", "trigger", "rule", "workflow_id", "status",
                 "result", "duration_ms", "timestamp")

    def __init__(self, trigger: str = "", rule: str = "",
                 workflow_id: str = "") -> None:
        self.record_id: str = f"er_{uuid.uuid4().hex[:8]}"
        self.trigger: str = trigger
        self.rule: str = rule
        self.workflow_id: str = workflow_id
        self.status: str = "unknown"
        self.result: Dict[str, Any] = {}
        self.duration_ms: float = 0.0
        self.timestamp: float = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {s: getattr(self, s) for s in self.__slots__}
