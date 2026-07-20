"""Custom exceptions for Prompt Evolution Engine."""

class PromptEvolutionError(Exception):
    """Base exception for prompt evolution system."""

class TemplateNotFoundError(PromptEvolutionError):
    """Template not found in memory."""

class StyleNotFoundError(PromptEvolutionError):
    """Style not found in library."""

class VariationLimitError(PromptEvolutionError):
    """Max variations reached."""

class PerformanceDataError(PromptEvolutionError):
    """Invalid performance data."""
