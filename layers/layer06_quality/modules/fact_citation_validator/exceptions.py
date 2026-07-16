"""Custom exceptions for Fact & Citation Validator."""
from __future__ import annotations


class FactValidationError(Exception):
    """Base exception for fact validation errors."""


class InvalidClaimError(FactValidationError):
    """Raised when claim parsing fails."""


class CitationFormatError(FactValidationError):
    """Raised when citation format is invalid."""


class ValidatorConfigError(FactValidationError):
    """Raised when validator configuration is invalid."""
