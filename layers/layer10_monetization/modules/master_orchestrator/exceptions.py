"""Custom exceptions for Master Orchestrator."""
from __future__ import annotations


class OrchestratorError(Exception):
    """Base exception for orchestrator errors."""


class WorkflowError(OrchestratorError):
    """Raised when workflow execution fails."""


class RoutingError(OrchestratorError):
    """Raised when layer routing fails."""


class DependencyError(OrchestratorError):
    """Raised when dependency resolution fails."""


class ExecutionError(OrchestratorError):
    """Raised when layer execution fails."""


class SchedulerError(OrchestratorError):
    """Raised when scheduling fails."""


class HealthError(OrchestratorError):
    """Raised when system health check fails."""
