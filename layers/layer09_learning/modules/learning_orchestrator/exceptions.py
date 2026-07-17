"""Custom exceptions for Learning Orchestrator."""
from __future__ import annotations


class LearningOrchestratorError(Exception):
    """Base exception for learning orchestrator errors."""


class PipelineError(LearningOrchestratorError):
    """Raised when the learning pipeline fails."""


class ModuleExecutionError(LearningOrchestratorError):
    """Raised when a specific module fails during execution."""


class AggregationError(LearningOrchestratorError):
    """Raised when result aggregation fails."""
