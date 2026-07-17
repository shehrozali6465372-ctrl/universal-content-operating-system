"""Custom exceptions for Strategy Optimization Engine."""
from __future__ import annotations


class StrategyOptimizationError(Exception):
    """Base exception for strategy optimization errors."""


class PatternDetectionError(StrategyOptimizationError):
    """Raised when pattern detection fails."""


class StrategyValidationError(StrategyOptimizationError):
    """Raised when strategy validation fails."""


class RecommendationError(StrategyOptimizationError):
    """Raised when recommendation generation fails."""
