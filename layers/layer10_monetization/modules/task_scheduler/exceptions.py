"""Custom exceptions for Task Scheduler Engine."""
from __future__ import annotations


class SchedulerError(Exception):
    """Base exception for scheduler errors."""


class TaskNotFoundError(SchedulerError):
    """Raised when a task is not found."""


class QueueFullError(SchedulerError):
    """Raised when the task queue is full."""


class WorkerUnavailableError(SchedulerError):
    """Raised when no workers are available."""


class ResourceUnavailableError(SchedulerError):
    """Raised when required resources are unavailable."""


class SchedulingTimeoutError(SchedulerError):
    """Raised when scheduling times out."""


class PolicyError(SchedulerError):
    """Raised when a scheduling policy fails."""
