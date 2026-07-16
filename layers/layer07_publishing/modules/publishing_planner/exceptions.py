"""Custom exceptions for Publishing Planner."""
from __future__ import annotations


class PlannerError(Exception):
    """Base exception for planner errors."""


class SchedulingError(PlannerError):
    """Raised when scheduling fails."""


class PlatformSelectionError(PlannerError):
    """Raised when platform selection fails."""
