"""Draft Generator — Custom Exceptions."""


class DraftGeneratorError(Exception):
    """Base exception for Draft Generator."""


class LLMProviderError(DraftGeneratorError):
    """Raised when LLM provider fails."""


class PromptBuildError(DraftGeneratorError):
    """Raised when prompt construction fails."""


class DraftValidationError(DraftGeneratorError):
    """Raised when generated draft fails validation."""


class RateLimitError(LLMProviderError):
    """Raised when LLM rate limit is hit."""


class ProviderNotConfiguredError(LLMProviderError):
    """Raised when LLM provider is not configured."""
