"""
Audience Research Exceptions
Layer 2: Research Engine — Module 4
"""


class AudienceResearchError(Exception):
    """Base exception for Audience Research module."""


class AudienceNotFoundError(AudienceResearchError):
    """Raised when an audience segment is not found."""


class DuplicateAudienceError(AudienceResearchError):
    """Raised when trying to add a duplicate audience segment."""


class InsufficientDataError(AudienceResearchError):
    """Raised when not enough data for analysis."""


class PredictionError(AudienceResearchError):
    """Raised when prediction fails."""
