"""
Competitor Analysis Exceptions
Layer 2: Research Engine — Module 3
"""


class CompetitorAnalysisError(Exception):
    """Base exception for Competitor Analysis module."""


class CompetitorNotFoundError(CompetitorAnalysisError):
    """Raised when a competitor is not found."""


class DuplicateCompetitorError(CompetitorAnalysisError):
    """Raised when trying to add a duplicate competitor."""


class AnalysisError(CompetitorAnalysisError):
    """Raised when analysis fails."""


class DataQualityError(CompetitorAnalysisError):
    """Raised when data quality is insufficient for analysis."""
