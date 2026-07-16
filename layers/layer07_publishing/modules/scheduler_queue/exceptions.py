"""Custom exceptions for Scheduler & Queue."""
from __future__ import annotations


class QueueError(Exception):
    """Base exception for queue errors."""


class JobNotFoundError(QueueError):
    """Raised when a job is not found."""


class QueueFullError(QueueError):
    """Raised when queue capacity is exceeded."""
