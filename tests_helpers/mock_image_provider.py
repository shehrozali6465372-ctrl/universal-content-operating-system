"""Test-only fake image provider; never import from production runtime."""
from __future__ import annotations

from typing import Any

from layers.layer05_image.modules.image_provider.image_provider import (
    BaseImageProvider,
    ImageResponse,
)


class MockImageProvider(BaseImageProvider):
    """Deterministic mock image provider for unit tests only."""

    def __init__(self) -> None:
        super().__init__(provider_name="mock")
        self._mock_url = "https://example.com/mock_image.png"

    def generate(
        self, prompt: str, size: str = "1024x1024", **kwargs: Any
    ) -> ImageResponse:
        response = ImageResponse()
        response.image_url = self._mock_url
        response.provider = "mock"
        response.model = "mock-v1"
        response.revised_prompt = prompt
        response.latency_ms = 1.0
        with self._counter_lock:
            self._call_count += 1
        return response

    def is_configured(self) -> bool:
        return True
