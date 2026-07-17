"""Custom exceptions for Self-Improvement Loop."""
from __future__ import annotations


class SelfImprovementError(Exception):
    """Base exception for self-improvement errors."""


class DetectionError(SelfImprovementError):
    """Raised when mistake detection fails."""


class ExperimentError(SelfImprovementError):
    """Raised when experiment operations fail."""


class RollbackError(SelfImprovementError):
    """Raised when rollback fails."""
