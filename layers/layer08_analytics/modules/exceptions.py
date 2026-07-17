"""Custom exceptions for Layer 8 Analytics."""
from __future__ import annotations


class AnalyticsError(Exception):
    """Base exception for analytics errors."""


class DataCollectionError(AnalyticsError):
    """Raised when data collection fails."""


class MetricCalculationError(AnalyticsError):
    """Raised when metric calculation fails."""


class ReportGenerationError(AnalyticsError):
    """Raised when report generation fails."""


class InsightError(AnalyticsError):
    """Raised when insight extraction fails."""
