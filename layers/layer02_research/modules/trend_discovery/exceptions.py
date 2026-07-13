"""
Trend Discovery Exceptions
Layer 2: Research Engine — Module 1
"""


class TrendError(Exception):
    """Base exception for trend discovery."""


class TrendSourceError(TrendError):
    """Raised when a trend source fails to fetch data."""


class TrendNotFoundError(TrendError):
    """Raised when a requested trend does not exist."""


class InvalidSourceError(TrendError):
    """Raised when an invalid source is referenced."""
