"""Custom exceptions for Failure Recovery Engine."""
from __future__ import annotations


class RecoveryError(Exception):
    """Base exception for recovery errors."""


class CircuitOpenError(RecoveryError):
    """Raised when circuit breaker is open."""


class RecoveryExhaustedError(RecoveryError):
    """Raised when all recovery attempts are exhausted."""


class RollbackFailedError(RecoveryError):
    """Raised when rollback itself fails."""
