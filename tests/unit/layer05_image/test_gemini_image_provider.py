"""Production-boundary tests for the Layer 5 Gemini image provider."""
from __future__ import annotations

import base64
import json
from pathlib import Path
from unittest.mock import patch
import urllib.error

import pytest

from layers.layer05_image.modules.image_provider.gemini_image_provider import GeminiImageProvider


def test_provider_fails_closed_without_credentials() -> None:
    provider = GeminiImageProvider(api_key=None)
    with patch.dict("os.environ", {}, clear=True):
        assert provider.is_configured() is False
        with pytest.raises(RuntimeError, match="not configured"):
            provider.generate("a product photo")


def test_deprecated_or_unsupported_models_are_rejected() -> None:
    provider = GeminiImageProvider(api_key="test", model="gemini-3-pro-image-preview")
    assert provider.is_configured() is False


def test_invalid_size_is_rejected() -> None:
    provider = GeminiImageProvider(api_key="test", model="gemini-3.1-flash-image")
    with pytest.raises(ValueError, match="WIDTHxHEIGHT"):
        provider._parse_size("bad-size")


def test_real_response_is_persisted_with_content_hash(tmp_path: Path) -> None:
    image_bytes = b"\x89PNG\r\n\x1a\nreal-image"
    body = {"steps": [{"type": "model_output", "content": [{
        "type": "image",
        "mime_type": "image/png",
        "data": base64.b64encode(image_bytes).decode("ascii"),
    }]}]}

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


def test_gemini_request_uses_current_image_config(tmp_path: Path) -> None:
    image_bytes = b"\\x89PNG\\r\\n\\x1a\\nrequest-contract"
    body = {"steps": [{"type": "model_output", "content": [{
        "type": "image",
        "mime_type": "image/png",
        "data": base64.b64encode(image_bytes).decode("ascii"),
    }]}]}

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

    assert captured["url"].endswith("/v1beta/interactions")
    assert captured["payload"]["model"] == "gemini-3.1-flash-image"
    assert captured["payload"]["input"][0]["type"] == "text"
    image_config = captured["payload"]["response_format"]
    assert image_config["type"] == "image"
    assert image_config["mime_type"] == "image/jpeg"
    assert image_config["aspect_ratio"] == "4:5"
    assert image_config["image_size"] == "2K"


def test_interactions_api_extracts_output_image(tmp_path: Path) -> None:
    image_bytes = b"\\x89PNG\\r\\n\\x1a\\ninteraction-output"
    body = {"output_image": {
        "data": base64.b64encode(image_bytes).decode("ascii"),
        "mime_type": "image/png",
    }}

    class FakeResponse:
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False
        def read(self):
            return json.dumps(body).encode("utf-8")

    provider = GeminiImageProvider(api_key="test")
    with patch.dict("os.environ", {"UCOS_IMAGE_OUTPUT_DIR": str(tmp_path)}):
        with patch(
            "layers.layer05_image.modules.image_provider.gemini_image_provider.urllib.request.urlopen",
            return_value=FakeResponse(),
        ):
            result = provider.generate("current API test")

    assert result.image_data == image_bytes
    assert Path(result.image_url).exists()
    assert result.metadata["mime_type"] == "image/png"


def test_rate_limit_rotates_configured_environment_keys(tmp_path: Path) -> None:
    image_bytes = b"\\x89PNG\\r\\n\\x1a\\nrotated"
    body = {"steps": [{"type": "model_output", "content": [{
        "type": "image",
        "mime_type": "image/png",
        "data": base64.b64encode(image_bytes).decode("ascii"),
    }]}]}
    class FakeResponse:
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False
        def read(self):
            return json.dumps(body).encode("utf-8")
    provider = GeminiImageProvider(api_key=None)
    calls = []
    def fake_urlopen(request, timeout):
        calls.append(request.headers["X-goog-api-key"])
        if len(calls) <= 4:
            raise urllib.error.HTTPError(request.full_url, 429, "rate", {}, None)
        return FakeResponse()
    with patch.dict("os.environ", {
        "GEMINI_API_KEY_1": "first",
        "GEMINI_API_KEY_2": "second",
        "UCOS_IMAGE_OUTPUT_DIR": str(tmp_path),
    }, clear=True):
        with patch(
            "layers.layer05_image.modules.image_provider.gemini_image_provider.urllib.request.urlopen",
            side_effect=fake_urlopen,
        ):
            result = provider.generate("rotation test", size="1024x1024")
    assert result.image_data == image_bytes
    assert calls[0] == "first"
    assert calls[-1] == "second"


def test_history_is_bounded_and_limit_is_validated() -> None:
    provider = GeminiImageProvider(api_key="test")
    for index in range(1005):
        provider._record_history({"index": index})
    assert len(provider.get_history(1000)) == 1000
    assert provider.get_history(1)[0]["index"] == 1004
    with pytest.raises(ValueError, match="between 1 and 1000"):
        provider.get_history(0)
    with pytest.raises(ValueError, match="between 1 and 1000"):
        provider.get_history(1001)
