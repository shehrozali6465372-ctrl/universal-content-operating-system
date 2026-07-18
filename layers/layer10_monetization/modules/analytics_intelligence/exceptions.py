"""Custom exceptions for Analytics Intelligence & Optimization Engine."""
from __future__ import annotations


class AnalyticsError(Exception):
    """Base exception for analytics errors."""


class CollectionError(AnalyticsError):
    """Raised when analytics collection fails."""


class NormalizationError(AnalyticsError):
    """Raised when analytics normalization fails."""


class OptimizationError(AnalyticsError):
    """Raised when optimization fails."""


class PredictionError(AnalyticsError):
    """Raised when analytics prediction fails."""


class StorageError(AnalyticsError):
    """Raised when analytics storage fails."""


class ReportError(AnalyticsError):
    """Raised when report generation fails."""


class AnalysisError(AnalyticsError):
    """Raised when analysis fails."""
