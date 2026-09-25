"""Production contract tests for Layer 5 orchestration."""
from __future__ import annotations

import pytest

from layers.layer05_image.modules.image_orchestrator.image_orchestrator import ImageOrchestrator
from layers.layer05_image.modules.image_provider.image_provider import (
    BaseImageProvider,
    ImageResponse,
)


class ConfiguredProvider(BaseImageProvider):
    """Deterministic provider for orchestration contract tests."""

    def __init__(self) -> None:
        super().__init__(provider_name="test-provider")

    def is_configured(self) -> bool:
        return True

    def generate(self, prompt: str, size: str = "1024x1024", **kwargs: object) -> ImageResponse:
        data = b"real-test-image"
        response = ImageResponse()
        response.image_url = "test://image"
        response.image_data = data
        response.provider = self.provider_name
        response.model = "test-model"
        response.metadata["sha256"] = __import__("hashlib").sha256(data).hexdigest()
        return response


def test_orchestrator_counts_successful_runs() -> None:
    orchestrator = ImageOrchestrator(provider=ConfiguredProvider())
    result = orchestrator.run("test topic")
    assert result.metadata["asset_sha256"]
    assert orchestrator.run_count == 1


def test_orchestrator_rejects_empty_platform_list() -> None:
    orchestrator = ImageOrchestrator(provider=ConfiguredProvider())
    with pytest.raises(ValueError, match="must not be empty"):
        orchestrator.run_multi_platform("topic", [])


def test_orchestrator_rejects_non_list_platforms() -> None:
    orchestrator = ImageOrchestrator(provider=ConfiguredProvider())
    with pytest.raises(ValueError, match="must be a list"):
        orchestrator.run_multi_platform("topic", "instagram")  # type: ignore[arg-type]


def test_orchestrator_rejects_mock_provider_result() -> None:
    class MockResultProvider(ConfiguredProvider):
        def generate(self, prompt: str, size: str = "1024x1024", **kwargs: object) -> ImageResponse:
            response = super().generate(prompt, size, **kwargs)
            response.provider = "mock"
            return response

    orchestrator = ImageOrchestrator(provider=MockResultProvider())
    with pytest.raises(RuntimeError, match="Mock image providers"):
        orchestrator.run("topic")
