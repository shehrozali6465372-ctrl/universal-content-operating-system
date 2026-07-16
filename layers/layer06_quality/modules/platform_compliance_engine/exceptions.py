"""Custom exceptions for Platform Compliance Engine."""
from __future__ import annotations


class ComplianceCheckError(Exception):
    """Base exception for compliance check errors."""


class PlatformConfigError(ComplianceCheckError):
    """Raised when platform configuration is invalid."""


class RuleViolationError(ComplianceCheckError):
    """Raised when content violates a platform rule."""
