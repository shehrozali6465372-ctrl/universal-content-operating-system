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


def test_reference_url_fails_closed_instead_of_being_treated_as_visual_input() -> None:
    provider = GeminiImageProvider(api_key="test")
    with pytest.raises(NotImplementedError, match="actual image bytes"):
        provider.generate_with_reference("product photo", reference_url="https://example.com/ref.png")


def test_gemini_request_uses_current_image_response_format(tmp_path: Path) -> None:
    image_bytes = b"\\x89PNG\\r\\n\\x1a\\nrequest-contract"
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

    provider = GeminiImageProvider(api_key="test")
    captured = {}

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["timeout"] = timeout
        captured["payload"] = json.loads(request.data.decode("utf-8"))
        return FakeResponse()

    with patch.dict("os.environ", {"UCOS_IMAGE_OUTPUT_DIR": str(tmp_path)}):
        with patch(
            "layers.layer05_image.modules.image_provider.gemini_image_provider.urllib.request.urlopen",
            side_effect=fake_urlopen,
        ):
            provider.generate("a product photo", size="1200x1500")

    assert captured["url"].endswith("/v1/models/gemini-3.1-flash-image:generateContent")
    assert captured["payload"]["generationConfig"]["responseModalities"] == ["IMAGE"]
    assert captured["payload"]["responseFormat"]["image"]["aspectRatio"] == "4:5"
    assert captured["payload"]["responseFormat"]["image"]["imageSize"] == "2K"
