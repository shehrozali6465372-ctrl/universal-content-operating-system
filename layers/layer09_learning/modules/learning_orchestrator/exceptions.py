"""Custom exceptions for the Layer 9 learning orchestrator."""
from __future__ import annotations


class LearningOrchestratorError(Exception):
    """Base exception for learning-orchestration failures."""


class PipelineError(LearningOrchestratorError):
    """Raised when the learning pipeline cannot be constructed or completed."""


class ModuleExecutionError(LearningOrchestratorError):
    """Raised when a learning module fails during execution."""


class AggregationError(LearningOrchestratorError):
    """Raised when stage results cannot be merged safely."""


class ProductionLearningDataRequired(LearningOrchestratorError):
    """Raised when a production learning run lacks observed data.

    Layer 9 must never manufacture feedback, performance outcomes, predictions,
    or optimization evidence merely to make an orchestration appear successful.
    """