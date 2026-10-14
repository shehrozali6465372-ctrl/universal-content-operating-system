"""Image Provider — Abstract interface for AI image generation providers."""
from __future__ import annotations
from abc import ABC, abstractmethod
from threading import RLock
from typing import Any, Dict, List


def parse_image_size(size: str) -> tuple[int, int]:
    """Parse and validate a WIDTHxHEIGHT image size shared by all providers."""
    try:
        width, height = (int(part) for part in size.lower().split("x", 1))
    except (ValueError, TypeError, AttributeError):
        raise ValueError("Image size must use WIDTHxHEIGHT notation") from None
    if not (256 <= width <= 4096 and 256 <= height <= 4096):
        raise ValueError("Image dimensions must be between 256 and 4096 pixels")
    return width, height


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
            "metadata": self.metadata,
        }


class BaseImageProvider(ABC):
    """Abstract base class for image providers."""

    def __init__(self, provider_name: str = "", api_key: str = "") -> None:
        self.provider_name = provider_name
        self.api_key = api_key
        self._call_count = 0
        self._counter_lock = RLock()

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
        with self._counter_lock:
            calls = self._call_count
        return {"provider": self.provider_name, "calls": calls}
