"""Custom exceptions for Publishing Policies."""
from __future__ import annotations


class PolicyError(Exception):
    """Base exception for policy errors."""


class PolicyViolationError(PolicyError):
    """Raised when content violates a policy."""


class PolicyNotFoundError(PolicyError):
    """Raised when a policy is not found."""
