"""Custom exceptions for Multi Model Intelligence."""
from __future__ import annotations


class MultiModelError(Exception):
    """Base error for multi-model system."""


class ConsensusError(MultiModelError):
    """Consensus engine failure."""


class VotingError(MultiModelError):
    """Voting engine failure."""


class RankingError(MultiModelError):
    """Ranking engine failure."""


class ParallelExecutionError(MultiModelError):
    """Parallel execution failure."""


class EnsembleError(MultiModelError):
    """Ensemble AI failure."""


class SelectionError(MultiModelError):
    """Response selection failure."""


class MergeError(MultiModelError):
    """Reasoning merge failure."""


class ConfidenceError(MultiModelError):
    """Confidence calculation failure."""


class ModelTimeoutError(MultiModelError):
    """Model response timeout."""


class AllModelsFailedError(MultiModelError):
    """All models returned errors."""


class InsufficientResponsesError(MultiModelError):
    """Not enough responses for consensus."""
