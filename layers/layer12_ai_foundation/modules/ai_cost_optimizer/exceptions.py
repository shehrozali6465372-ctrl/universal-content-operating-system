"""Custom exceptions for AI Cost Optimizer."""
from __future__ import annotations
class CostError(Exception):
    """Base error for cost optimizer."""
class BudgetExceededError(CostError):
    """Budget limit exceeded."""
class TrackingError(CostError):
    """Cost tracking failure."""
class OptimizationError(CostError):
    """Cost optimization failure."""
class PredictionError(CostError):
    """Cost prediction failure."""
class ReportError(CostError):
    """Report generation failure."""
