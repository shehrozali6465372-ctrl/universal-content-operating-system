"""LLM Provider — Base interface for LLM providers."""
from __future__ import annotations
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List


class LLMResponse:
    """Response from an LLM provider."""
    __slots__ = ("text", "model", "tokens_used", "latency_ms",
                 "finish_reason", "metadata")

    def __init__(self, text: str = "") -> None:
        self.text = text
        self.model = ""
        self.tokens_used = 0
        self.latency_ms = 0.0
        self.finish_reason = "stop"
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "model": self.model,
            "tokens_used": self.tokens_used,
            "latency_ms": round(self.latency_ms, 2),
            "finish_reason": self.finish_reason,
        }


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""

    def __init__(self, provider_name: str = "", api_key: str = "",
                 model: str = "", max_tokens: int = 1000,
                 temperature: float = 0.7) -> None:
        self.provider_name = provider_name
        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self._call_count = 0
        self._total_tokens = 0
        self._total_latency_ms = 0.0

    @abstractmethod
    def generate(self, prompt: str, system_prompt: str = "",
                 **kwargs: Any) -> LLMResponse:
        """Generate text from a prompt."""
        ...

    @abstractmethod
    def is_configured(self) -> bool:
        """Check if provider is properly configured."""
        ...

    def generate_batch(self, prompts: List[str], system_prompt: str = "") -> List[LLMResponse]:
        """Generate text for multiple prompts."""
        return [self.generate(p, system_prompt) for p in prompts]

    def _record_call(self, tokens: int, latency: float) -> None:
        self._call_count += 1
        self._total_tokens += tokens
        self._total_latency_ms += latency

    @property
    def stats(self) -> Dict[str, Any]:
        return {
            "provider": self.provider_name,
            "calls": self._call_count,
            "total_tokens": self._total_tokens,
            "avg_latency_ms": round(self._total_latency_ms / max(self._call_count, 1), 2),
        }


class MockLLMProvider(BaseLLMProvider):
    """Mock LLM provider for testing."""

    def __init__(self, response: str = "Mock draft content.", **kwargs: Any) -> None:
        super().__init__(provider_name="mock", **kwargs)
        self._mock_response = response
        self._responses: List[str] = []
        self._call_index = 0

    def generate(self, prompt: str, system_prompt: str = "",
                 **kwargs: Any) -> LLMResponse:
        start = time.time()
        if self._responses:
            text = self._responses[self._call_index % len(self._responses)]
            self._call_index += 1
        else:
            text = self._mock_response
        latency = (time.time() - start) * 1000
        self._record_call(tokens=len(text.split()), latency=latency)
        resp = LLMResponse(text=text)
        resp.model = "mock-model"
        resp.tokens_used = len(text.split())
        resp.latency_ms = latency
        return resp

    def is_configured(self) -> bool:
        return True

    def set_responses(self, responses: List[str]) -> None:
        self._responses = responses
        self._call_index = 0
