"""Image Provider — Abstract interface for AI image generation providers."""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict, List


class ImageResponse:
    """Response from an image generation provider."""
    __slots__ = ("image_url", "image_data", "provider", "model",
                 "revised_prompt", "latency_ms", "metadata")

    def __init__(self) -> None:
        self.image_url = ""
        self.image_data: bytes = b""
        self.provider = ""
        self.model = ""
        self.revised_prompt = ""
        self.latency_ms = 0.0
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "image_url": self.image_url,
            "provider": self.provider,
            "model": self.model,
            "latency_ms": round(self.latency_ms, 2),
        }


class BaseImageProvider(ABC):
    """Abstract base class for image providers."""

    def __init__(self, provider_name: str = "", api_key: str = "") -> None:
        self.provider_name = provider_name
        self.api_key = api_key
        self._call_count = 0

    @abstractmethod
    def generate(self, prompt: str, size: str = "1024x1024",
                 **kwargs: Any) -> ImageResponse:
        """Generate an image from a prompt."""
        ...

    @abstractmethod
    def is_configured(self) -> bool:
        """Check if provider is configured."""
        ...

    def generate_batch(self, prompts: List[str], size: str = "1024x1024") -> List[ImageResponse]:
        """Generate multiple images."""
        return [self.generate(p, size) for p in prompts]

    @property
    def stats(self) -> Dict[str, Any]:
        return {"provider": self.provider_name, "calls": self._call_count}


class MockImageProvider(BaseImageProvider):
    """Mock image provider for testing."""

    def __init__(self) -> None:
        super().__init__(provider_name="mock")
        self._mock_url = "https://example.com/mock_image.png"

    def generate(self, prompt: str, size: str = "1024x1024",
                 **kwargs: Any) -> ImageResponse:
        resp = ImageResponse()
        resp.image_url = self._mock_url
        resp.provider = "mock"
        resp.model = "mock-v1"
        resp.revised_prompt = prompt
        resp.latency_ms = 1.0
        self._call_count += 1
        return resp

    def is_configured(self) -> bool:
        return True
