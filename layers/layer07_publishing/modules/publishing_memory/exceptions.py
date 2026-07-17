"""Custom exceptions for Publishing Memory."""
from __future__ import annotations


class MemoryError(Exception):
    """Base exception for memory errors."""


class StorageError(MemoryError):
    """Raised when storage operation fails."""


class SearchError(MemoryError):
    """Raised when search fails."""
