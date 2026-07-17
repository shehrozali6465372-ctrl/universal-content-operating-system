"""Custom exceptions for Quality Calibration Engine."""
from __future__ import annotations


class CalibrationError(Exception):
    """Base exception for calibration errors."""


class ThresholdError(CalibrationError):
    """Raised when threshold operations fail."""


class BenchmarkError(CalibrationError):
    """Raised when benchmark operations fail."""


class ValidationError(CalibrationError):
    """Raised when calibration validation fails."""
