"""Custom exceptions for Quality Scoring & Confidence Engine."""
from __future__ import annotations


class ScoringError(Exception):
    """Base exception for scoring errors."""


class InsufficientDataError(ScoringError):
    """Raised when not enough module data is available."""
