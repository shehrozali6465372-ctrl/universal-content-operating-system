"""Custom exceptions for Plagiarism & Originality Engine."""
from __future__ import annotations


class PlagiarismCheckError(Exception):
    """Base exception for plagiarism check errors."""


class OriginalityScoreError(PlagiarismCheckError):
    """Raised when originality scoring fails."""


class SelfPlagiarismError(PlagiarismCheckError):
    """Raised when self-plagiarism check fails."""
