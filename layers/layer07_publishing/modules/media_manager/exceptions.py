"""Custom exceptions for Media Manager."""
from __future__ import annotations


class MediaError(Exception):
    """Base exception for media errors."""


class MediaValidationError(MediaError):
    """Raised when media fails validation."""


class MediaOptimizationError(MediaError):
    """Raised when media optimization fails."""
