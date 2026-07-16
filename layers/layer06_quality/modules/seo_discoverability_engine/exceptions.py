"""Custom exceptions for SEO & Discoverability Engine."""
from __future__ import annotations


class SEOCheckError(Exception):
    """Base exception for SEO check errors."""


class KeywordAnalysisError(SEOCheckError):
    """Raised when keyword analysis fails."""


class MetadataError(SEOCheckError):
    """Raised when metadata check fails."""
