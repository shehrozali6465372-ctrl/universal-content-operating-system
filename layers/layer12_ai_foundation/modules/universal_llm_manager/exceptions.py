"""Exceptions for universal_llm_manager."""
from __future__ import annotations

class AIError(Exception): """Base AI error."""
class LLMError(AIError): """LLMError."""
class ProviderError(AIError): """ProviderError."""
class ModelNotFoundError(AIError): """ModelNotFoundError."""
class RateLimitError(AIError): """RateLimitError."""
class TokenLimitError(AIError): """TokenLimitError."""
class AuthenticationError(AIError): """AuthenticationError."""
class TimeoutError(AIError): """TimeoutError."""
class QuotaExceededError(AIError): """QuotaExceededError."""
