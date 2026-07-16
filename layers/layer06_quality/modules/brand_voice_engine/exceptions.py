"""Custom exceptions for Brand Voice & Consistency Engine."""
from __future__ import annotations


class BrandVoiceError(Exception):
    """Base exception for brand voice errors."""


class ProfileLoadError(BrandVoiceError):
    """Raised when brand profile cannot be loaded."""


class VoiceMismatchError(BrandVoiceError):
    """Raised when content doesn't match brand voice."""
