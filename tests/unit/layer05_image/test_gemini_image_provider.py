"""Production-boundary tests for the Layer 5 Gemini image provider."""
from __future__ import annotations

import base64
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from layers.layer05_image.modules.image_provider.gemini_image_provider import GeminiImageProvider


def test_provider_fails_closed_without_credentials() -> None:
    provider = GeminiImageProvider(api_key=None)
    with patch.dict("os.environ", {}, clear=True):
        assert provider.is_configured() is False
        with pytest.raises(RuntimeError, match="not configured"):
            provider.generate("a product photo")


def test_invalid_size_is_rejected() -> None:
    provider = GeminiImageProvider(api_key="test", model="gemini-3.1-flash-image")
    with pytest.raises(ValueError, match="WIDTHxHEIGHT"):
        provider._parse_size("bad-size")


def test_real_response_is_persisted_with_content_hash(tmp_path: Path) -> None:
    image_bytes = b"\x89PNG\r\n\x1a\nreal-image"
    body = {"candidates": [{"content": {"parts": [{"inlineData": {
        "mimeType": "image/png",
        "data": base64.b64encode(image_bytes).decode("ascii"),
    }}]}}]}

    class FakeResponse:
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False
        def read(self):
            return json.dumps(body).encode("utf-8")

    provider = GeminiImageProvider(api_key="test", model="gemini-3.1-flash-image")
    with patch.dict("os.environ", {"UCOS_IMAGE_OUTPUT_DIR": str(tmp_path)}):
        with patch(
            "layers.layer05_image.modules.image_provider.gemini_image_provider.urllib.request.urlopen",
            return_value=FakeResponse(),
        ):
            result = provider.generate("a product photo", size="1024x1024")

    assert result.image_data == image_bytes
    assert result.provider == "gemini"
    assert Path(result.image_url).exists()
    assert result.metadata["mime_type"] == "image/png"
    assert result.metadata["sha256"]
