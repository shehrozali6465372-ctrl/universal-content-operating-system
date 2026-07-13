"""
Topic Scoring Exceptions
Layer 2: Research Engine — Module 8
"""


class TopicScoringError(Exception):
    """Base exception for Topic Scoring module."""


class InvalidScoreError(TopicScoringError):
    """Raised when score values are invalid."""


class WeightError(TopicScoringError):
    """Raised when weight configuration is invalid."""
