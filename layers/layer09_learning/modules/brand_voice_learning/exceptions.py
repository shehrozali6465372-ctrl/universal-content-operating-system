"""Custom exceptions for Brand Voice Learning Engine."""
from __future__ import annotations


class BrandVoiceError(Exception):
    """Base exception for brand voice errors."""


class AnalysisError(BrandVoiceError):
    """Raised when voice analysis fails."""


class ConsistencyError(BrandVoiceError):
    """Raised when consistency checking fails."""


class LearningError(BrandVoiceError):
    """Raised when voice learning fails."""
