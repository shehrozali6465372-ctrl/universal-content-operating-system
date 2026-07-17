"""Custom exceptions for Content Optimization Engine."""
from __future__ import annotations


class ContentOptimizationError(Exception):
    """Base exception for content optimization errors."""


class AnalysisError(ContentOptimizationError):
    """Raised when content analysis fails."""


class RewriteError(ContentOptimizationError):
    """Raised when rewriting fails."""


class ValidationError(ContentOptimizationError):
    """Raised when validation fails."""
