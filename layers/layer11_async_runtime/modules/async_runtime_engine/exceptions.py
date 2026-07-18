"""Exceptions for Async Runtime Engine."""
from __future__ import annotations


class AsyncRuntimeError(Exception):
    """Base exception for async runtime errors."""


class EventLoopError(AsyncRuntimeError):
    """Raised when event loop operations fail."""


class TaskError(AsyncRuntimeError):
    """Raised when task operations fail."""


class WorkerError(AsyncRuntimeError):
    """Raised when worker operations fail."""


class TimeoutError(AsyncRuntimeError):
    """Raised when operations timeout."""


class CancellationError(AsyncRuntimeError):
    """Raised when tasks are cancelled."""


class SchedulerError(AsyncRuntimeError):
    """Raised when scheduling fails."""


class ResourceExhaustedError(AsyncRuntimeError):
    """Raised when resources are exhausted."""


class ConfigurationError(AsyncRuntimeError):
    """Raised when configuration is invalid."""


class HealthCheckError(AsyncRuntimeError):
    """Raised when health checks fail."""
