"""Custom exceptions for Memory Evolution Engine."""
from __future__ import annotations


class MemoryEvolutionError(Exception):
    """Base exception for memory evolution errors."""


class ClassificationError(MemoryEvolutionError):
    """Raised when classification fails."""


class MergeError(MemoryEvolutionError):
    """Raised when merge fails."""


class ArchiveError(MemoryEvolutionError):
    """Raised when archive operations fail."""
