"""Custom exceptions for Quality Orchestrator."""
from __future__ import annotations


class OrchestratorError(Exception):
    """Base exception for orchestrator errors."""


class ModuleExecutionError(OrchestratorError):
    """Raised when a module fails to execute."""


class PipelineError(OrchestratorError):
    """Raised when the pipeline fails."""
