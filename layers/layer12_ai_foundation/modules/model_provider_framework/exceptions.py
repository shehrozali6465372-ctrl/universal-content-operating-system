"""Exceptions for model_provider_framework."""
from __future__ import annotations


class ProviderFrameworkError(Exception):
    """Base exception for provider framework."""


class ProviderNotFoundError(ProviderFrameworkError):
    """Provider not found in registry."""


class ProviderInitializationError(ProviderFrameworkError):
    """Provider failed to initialize."""


class ProviderUnavailableError(ProviderFrameworkError):
    """Provider is currently unavailable."""


class ProviderRateLimitError(ProviderFrameworkError):
    """Provider rate limit exceeded."""


class ProviderAuthenticationError(ProviderFrameworkError):
    """Provider authentication failed."""


class ProviderTimeoutError(ProviderFrameworkError):
    """Provider request timed out."""


class ProviderCostLimitError(ProviderFrameworkError):
    """Provider cost limit exceeded."""


class ProviderValidationError(ProviderFrameworkError):
    """Provider request validation failed."""


class ProviderCacheError(ProviderFrameworkError):
    """Provider cache operation failed."""


class ProviderFallbackExhaustedError(ProviderFrameworkError):
    """All fallback providers exhausted."""
