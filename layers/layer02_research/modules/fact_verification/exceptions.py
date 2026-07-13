"""
Fact Verification Exceptions
Layer 2: Research Engine — Module 6
"""


class FactVerificationError(Exception):
    """Base exception for Fact Verification module."""


class ClaimExtractionError(FactVerificationError):
    """Raised when claim extraction fails."""


class VerificationError(FactVerificationError):
    """Raised when verification fails."""


class SourceValidationError(FactVerificationError):
    """Raised when source validation fails."""
