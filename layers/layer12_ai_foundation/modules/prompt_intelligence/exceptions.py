"""Custom exceptions for Prompt Intelligence."""
from __future__ import annotations


class PromptIntelligenceError(Exception):
    """Base error for prompt intelligence system."""


class OptimizationError(PromptIntelligenceError):
    """Prompt optimization failure."""


class TemplateError(PromptIntelligenceError):
    """Template rendering failure."""


class FewShotError(PromptIntelligenceError):
    """Few-shot selection failure."""


class PromptBuildError(PromptIntelligenceError):
    """Prompt construction failure."""


class PromptValidationError(PromptIntelligenceError):
    """Prompt validation failure."""


class MemoryError(PromptIntelligenceError):
    """Prompt memory failure."""


class ChainOfThoughtError(PromptIntelligenceError):
    """CoT reasoning failure."""
