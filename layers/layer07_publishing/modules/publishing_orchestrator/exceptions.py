"""Custom exceptions for Publishing Orchestrator."""
from __future__ import annotations


class OrchestratorError(Exception):
    """Base exception for orchestrator errors."""


class PipelineError(OrchestratorError):
    """Raised when pipeline execution fails."""


class IntegrationError(OrchestratorError):
    """Raised when module integration fails."""
