"""Custom exceptions for Scheduler & Workflow Orchestrator."""


class SchedulerError(Exception):
    """Base scheduler error."""


class WorkflowError(SchedulerError):
    """Workflow execution error."""


class SchedulingError(SchedulerError):
    """Task scheduling error."""


class QueueError(SchedulerError):
    """Queue management error."""


class DependencyError(SchedulerError):
    """Workflow dependency error."""


class ExecutionError(SchedulerError):
    """Workflow execution failure."""


class RetryError(SchedulerError):
    """Retry mechanism error."""


class RecoveryError(SchedulerError):
    """Recovery system error."""


class MonitoringError(SchedulerError):
    """Monitoring system error."""


class EventError(SchedulerError):
    """Event system error."""


class NotificationError(SchedulerError):
    """Notification system error."""
