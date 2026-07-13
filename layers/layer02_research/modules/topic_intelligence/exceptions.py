"""
Topic Intelligence Exceptions
Layer 2: Research Engine — Module 2
"""


class TopicIntelError(Exception):
    """Base exception for Topic Intelligence module."""


class TopicNotFoundError(TopicIntelError):
    """Raised when a topic is not found."""


class DuplicateTopicError(TopicIntelError):
    """Raised when trying to add a duplicate topic."""


class InvalidScoringError(TopicIntelError):
    """Raised when scoring parameters are invalid."""


class ClusterError(TopicIntelError):
    """Raised when clustering fails."""
