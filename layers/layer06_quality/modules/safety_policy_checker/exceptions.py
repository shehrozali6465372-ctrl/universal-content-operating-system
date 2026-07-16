"""Custom exceptions for Safety & Policy Checker."""
from __future__ import annotations


class SafetyCheckError(Exception):
    """Base exception for safety check errors."""


class PolicyViolationError(SafetyCheckError):
    """Raised when content violates platform policy."""


class HarmfulContentError(SafetyCheckError):
    """Raised when harmful content is detected."""


class SafetyConfigError(SafetyCheckError):
    """Raised when safety configuration is invalid."""
