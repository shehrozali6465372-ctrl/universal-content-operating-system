"""
Research Orchestrator Exceptions
Layer 2: Research Engine — Module 10
"""


class OrchestratorError(Exception):
    """Base exception for Research Orchestrator module."""


class WorkflowError(OrchestratorError):
    """Raised when a workflow operation fails."""


class StateError(OrchestratorError):
    """Raised on invalid state transitions."""


class CheckpointError(OrchestratorError):
    """Raised when checkpoint save/restore fails."""


class RetryExhaustedError(OrchestratorError):
    """Raised when all retry attempts are exhausted."""


class ExecutionCancelledError(OrchestratorError):
    """Raised when execution is cancelled."""


class PipelineError(OrchestratorError):
    """Raised when pipeline setup or execution fails."""
