"""Custom exceptions for Prompt Optimization Engine."""
from __future__ import annotations


class PromptOptimizationError(Exception):
    """Base exception for prompt optimization errors."""


class ValidationFailedError(PromptOptimizationError):
    """Raised when prompt validation fails."""


class OptimizationError(PromptOptimizationError):
    """Raised when optimization process fails."""


class HistoryError(PromptOptimizationError):
    """Raised when history operations fail."""


class MemoryError(PromptOptimizationError):
    """Raised when memory storage fails."""
