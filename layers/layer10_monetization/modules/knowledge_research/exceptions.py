"""Custom exceptions for Knowledge & Research Intelligence."""
from __future__ import annotations


class ResearchError(Exception):
    """Base exception for research errors."""


class SourceUnavailableError(ResearchError):
    """Raised when a research source is unavailable."""


class TrendDetectionError(ResearchError):
    """Raised when trend detection fails."""


class VerificationError(ResearchError):
    """Raised when fact verification fails."""


class KnowledgeError(ResearchError):
    """Raised when knowledge graph operations fail."""


class MemoryError(ResearchError):
    """Raised when research memory operations fail."""


class ValidationError(ResearchError):
    """Raised when research validation fails."""


class ResearchTimeoutError(ResearchError):
    """Raised when research times out."""
