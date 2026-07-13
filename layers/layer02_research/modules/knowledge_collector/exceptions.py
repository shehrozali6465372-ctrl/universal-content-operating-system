"""
Knowledge Collector Exceptions
Layer 2: Research Engine — Module 5
"""


class KnowledgeCollectorError(Exception):
    """Base exception for Knowledge Collector module."""


class EntryNotFoundError(KnowledgeCollectorError):
    """Raised when a knowledge entry is not found."""


class DuplicateEntryError(KnowledgeCollectorError):
    """Raised when trying to add a duplicate entry."""


class SourceError(KnowledgeCollectorError):
    """Raised when a source fails."""


class CacheError(KnowledgeCollectorError):
    """Raised when cache operation fails."""
