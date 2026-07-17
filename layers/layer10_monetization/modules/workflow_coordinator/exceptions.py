"""Custom exceptions for Workflow Coordinator."""
from __future__ import annotations


class WorkflowCoordinatorError(Exception):
    """Base exception for workflow coordinator errors."""


class StageExecutionError(WorkflowCoordinatorError):
    """Raised when a workflow stage fails."""


class SynchronizationError(WorkflowCoordinatorError):
    """Raised when synchronization fails."""


class CheckpointError(WorkflowCoordinatorError):
    """Raised when checkpoint operations fail."""


class StateError(WorkflowCoordinatorError):
    """Raised when state management fails."""


class TimeoutError(WorkflowCoordinatorError):
    """Raised when a stage or workflow times out."""


class RetryLimitExceeded(WorkflowCoordinatorError):
    """Raised when maximum retries are exhausted."""
