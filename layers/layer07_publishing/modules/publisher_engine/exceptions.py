"""Custom exceptions for Publisher Engine."""
from __future__ import annotations


class PublishError(Exception):
    """Base exception for publish errors."""


class PublishValidationError(PublishError):
    """Raised when publish request fails validation."""


class PublishExecutionError(PublishError):
    """Raised when publish execution fails."""


class UploadError(PublishError):
    """Raised when media upload fails."""


class RollbackError(PublishError):
    """Raised when rollback fails."""
