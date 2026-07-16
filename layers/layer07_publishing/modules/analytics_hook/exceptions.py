"""Custom exceptions for Analytics Hook."""
from __future__ import annotations


class AnalyticsError(Exception):
    """Base exception for analytics errors."""


class FetchError(AnalyticsError):
    """Raised when analytics fetch from platform fails."""


class NormalizationError(AnalyticsError):
    """Raised when metrics cannot be normalized."""
