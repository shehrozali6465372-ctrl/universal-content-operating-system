"""Custom exceptions for Human Review & Approval Engine."""
from __future__ import annotations


class ReviewError(Exception):
    """Base exception for review errors."""


class ApprovalError(ReviewError):
    """Raised when approval process fails."""


class WorkflowError(ReviewError):
    """Raised when workflow transition is invalid."""


class AuditError(ReviewError):
    """Raised when audit log fails."""
