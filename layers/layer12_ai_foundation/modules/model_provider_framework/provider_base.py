"""provider_base.py — Abstract base class for all AI providers."""
from __future__ import annotations
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class ProviderResponse:
    """Standard response from any provider."""
    __slots__ = ("content", "model", "provider", "usage", "latency_ms",
                 "finish_reason", "metadata", "request_id", "timestamp")

    def __init__(self, content: str, model: str, provider: str) -> None:
        self.content = content
        self.model = model
        self.provider = provider
        self.usage: Dict[str, int] = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        self.latency_ms: float = 0.0
        self.finish_reason: str = "stop"
        self.metadata: Dict[str, Any] = {}
        self.request_id: str = ""
        self.timestamp: float = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {"content": self.content, "model": self.model, "provider": self.provider,
                "usage": self.usage, "latency_ms": self.latency_ms,
                "finish_reason": self.finish_reason, "request_id": self.request_id}


class ProviderRequest:
    """Standard request to any provider."""
    __slots__ = ("prompt", "model", "messages", "temperature", "max_tokens",
                 "system_prompt", "stream", "stop", "provider", "metadata")

    def __init__(self, prompt: str = "", model: str = "", provider: str = "") -> None:
        self.prompt = prompt
        self.model = model
        self.messages: List[Dict[str, str]] = []
        self.temperature: float = 0.7
        self.max_tokens: int = 4096
        self.system_prompt: str = ""
        self.stream: bool = False
        self.stop: Optional[List[str]] = None
        self.provider = provider
        self.metadata: Dict[str, Any] = {}


class BaseProvider(ABC):
    """Abstract base class for all AI model providers."""

    __slots__ = ("_name", "_supported_models", "_config", "_is_initialized",
                 "_metrics", "_health_status")

    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None) -> None:
        self._name = name
        self._supported_models: List[str] = []
        self._config = config or {}
        self._is_initialized = False
        self._metrics: Dict[str, Any] = {"requests": 0, "errors": 0, "total_tokens": 0}
        self._health_status: str = "unknown"

    @property
    def name(self) -> str:
        return self._name

    @property
    def supported_models(self) -> List[str]:
        return list(self._supported_models)

    @property
    def is_initialized(self) -> bool:
        return self._is_initialized

    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the provider (validate keys, test connection)."""
        ...

    @abstractmethod
    def generate(self, request: ProviderRequest) -> ProviderResponse:
        """Generate a completion."""
        ...

    @abstractmethod
    def chat(self, messages: List[Dict[str, str]], model: str = "") -> ProviderResponse:
        """Chat completion."""
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is available."""
        ...

    def validate_model(self, model: str) -> bool:
        return model in self._supported_models or not self._supported_models

    def get_model_info(self, model: str) -> Dict[str, Any]:
        return {"model": model, "provider": self._name, "supported": self.validate_model(model)}

    def get_stats(self) -> Dict[str, Any]:
        return {"name": self._name, "initialized": self._is_initialized,
                "health": self._health_status, "metrics": dict(self._metrics)}

    def reset_metrics(self) -> None:
        self._metrics = {"requests": 0, "errors": 0, "total_tokens": 0}
