"""Custom exceptions for AI Reasoning Engine."""
from __future__ import annotations


class ReasoningError(Exception):
    """Base error for reasoning engine."""


class LogicalReasoningError(ReasoningError):
    """Logical reasoning failure."""


class AnalyticalReasoningError(ReasoningError):
    """Analytical reasoning failure."""


class CreativeReasoningError(ReasoningError):
    """Creative reasoning failure."""


class StrategicReasoningError(ReasoningError):
    """Strategic reasoning failure."""


class ReflectionError(ReasoningError):
    """Self-reflection failure."""


class DecisionError(ReasoningError):
    """Decision-making failure."""


class VerificationError(ReasoningError):
    """Reasoning verification failure."""


class ReasoningTimeoutError(ReasoningError):
    """Reasoning operation timed out."""


class ReasoningChainError(ReasoningError):
    """Reasoning chain broken."""
