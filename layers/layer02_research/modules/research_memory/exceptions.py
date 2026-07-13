"""
Research Memory Exceptions
Layer 2: Research Engine — Module 7
"""


class ResearchMemoryError(Exception):
    """Base exception for Research Memory module."""


class EntryNotFoundError(ResearchMemoryError):
    """Raised when a research entry is not found."""


class SearchError(ResearchMemoryError):
    """Raised when search fails."""


class GraphError(ResearchMemoryError):
    """Raised when graph operation fails."""
