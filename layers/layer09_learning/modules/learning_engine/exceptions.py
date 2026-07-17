"""Custom exceptions for Learning Engine."""
from __future__ import annotations


class LearningError(Exception):
    """Base exception for learning errors."""


class SignalCollectionError(LearningError):
    """Raised when signal collection fails."""


class LessonGenerationError(LearningError):
    """Raised when lesson generation fails."""


class MemoryStorageError(LearningError):
    """Raised when memory storage fails."""
