"""Custom exceptions for Engagement Predictor Engine."""
from __future__ import annotations


class EngagementPredictionError(Exception):
    """Base exception for engagement prediction errors."""


class FeatureExtractionError(EngagementPredictionError):
    """Raised when feature extraction fails."""


class PredictionError(EngagementPredictionError):
    """Raised when prediction computation fails."""


class ValidationError(EngagementPredictionError):
    """Raised when prediction validation fails."""
