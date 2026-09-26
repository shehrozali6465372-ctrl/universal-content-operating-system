"""Production-boundary tests for the Layer 5 OpenRouter image provider."""
from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from layers.layer05_image.modules.image_provider.openrouter_image_provider import (
    OpenRouterImageProvider,
)

PNG_BYTES = b"\x89PNG\r\n\x1a\nreal-openrouter-image"


class FakeResponse:
    def __init__(self, body: dict) -> None:
        self._body = body

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return json.dumps(self._body).encode("utf-8")


def test_provider_fails_closed_without_credentials() -> None:
    provider = OpenRouterImageProvider(api_key=None)
    with patch.dict("os.environ", {}, clear=True):
        assert provider.is_configured() is False
        with pytest.raises(RuntimeError, match="not configured"):
            provider.generate("a product photo")


def test_request_contract_and_real_response_persistence(tmp_path: Path) -> None:
    body = {
        "data": [{
            "b64_json": base64.b64encode(PNG_BYTES).decode("ascii"),
            "media_type": "image/png",
        }],
        "usage": {"cost": 0.04},
    }
    provider = OpenRouterImageProvider(api_key="test", model="bytedance-seed/seedream-4.5")
    captured = {}

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["timeout"] = timeout
        captured["headers"] = dict(request.headers)
        captured["payload"] = json.loads(request.data.decode("utf-8"))
        return FakeResponse(body)

    with patch.dict("os.environ", {"UCOS_IMAGE_OUTPUT_DIR": str(tmp_path)}):
        with patch(
            "layers.layer05_image.modules.image_provider.openrouter_image_provider.urllib.request.urlopen",
            side_effect=fake_urlopen,
        ):
            result = provider.generate("a product photo", size="1200x1500")

    assert captured["url"] == "https://openrouter.ai/api/v1/images"
    assert captured["timeout"] == 120
    assert captured["payload"] == {
        "model": "bytedance-seed/seedream-4.5",
        "prompt": "a product photo",
        "resolution": "2K",
        "aspect_ratio": "4:5",
        "n": 1,
    }
    assert "Authorization" in captured["headers"]
    assert captured["headers"]["Authorization"].startswith("Bearer ")
    assert result.image_data == PNG_BYTES
    assert result.provider == "openrouter"
    assert result.model == "bytedance-seed/seedream-4.5"
    assert result.metadata["mime_type"] == "image/png"
    assert result.metadata["sha256"]
    assert result.metadata["cost"] == 0.04
    assert Path(result.image_url).is_file()
    assert Path(result.image_url).read_bytes() == PNG_BYTES


def test_invalid_size_is_rejected_before_network_call() -> None:
    provider = OpenRouterImageProvider(api_key="test")
    with patch(
        "layers.layer05_image.modules.image_provider.openrouter_image_provider.urllib.request.urlopen"
    ) as urlopen:
        with pytest.raises(ValueError, match="WIDTHxHEIGHT"):
            provider.generate("photo", size="bad-size")
    urlopen.assert_not_called()


@pytest.mark.parametrize(
    ("status", "message"),
    [
        (401, "authentication failed"),
        (402, "insufficient credits"),
        (429, "rate limit exceeded"),
    ],
)
def test_known_http_failures_are_explicit(status: int, message: str) -> None:
    from urllib.error import HTTPError
    provider = OpenRouterImageProvider(api_key="test")

    error = HTTPError("https://openrouter.ai/api/v1/images", status, "error", {}, None)
    with patch(
        "layers.layer05_image.modules.image_provider.openrouter_image_provider.urllib.request.urlopen",
        side_effect=error,
    ):
        with pytest.raises(RuntimeError, match=message):
            provider.generate("photo")


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"data": []},
        {"data": [{}]},
        {"data": [{"b64_json": "not-base64", "media_type": "image/png"}]},
        {"data": [{"b64_json": base64.b64encode(b"not-an-image").decode("ascii"),
                   "media_type": "image/png"}]},
        {"data": [{"b64_json": base64.b64encode(PNG_BYTES).decode("ascii"),
                   "media_type": "text/plain"}]},
    ],
)
def test_malformed_success_responses_fail_closed(body: dict) -> None:
    provider = OpenRouterImageProvider(api_key="test")
    with patch(
        "layers.layer05_image.modules.image_provider.openrouter_image_provider.urllib.request.urlopen",
        return_value=FakeResponse(body),
    ):
        with pytest.raises(RuntimeError):
            provider.generate("photo")


def test_empty_prompt_is_rejected() -> None:
    provider = OpenRouterImageProvider(api_key="test")
    with pytest.raises(ValueError, match="must not be empty"):
        provider.generate("   ")


def test_transport_and_invalid_json_fail_closed() -> None:
    from urllib.error import URLError

    provider = OpenRouterImageProvider(api_key="test")
    patch_target = (
        "layers.layer05_image.modules.image_provider.openrouter_image_provider."
        "urllib.request.urlopen"
    )
    with patch(patch_target, side_effect=URLError("network down")):
        with pytest.raises(RuntimeError, match="transport failed"):
            provider.generate("photo")

    class InvalidJsonResponse(FakeResponse):
        def read(self):
            return b"not-json"

    with patch(patch_target, return_value=InvalidJsonResponse({})):
        with pytest.raises(RuntimeError, match="invalid JSON"):
            provider.generate("photo")


def test_persisted_hash_matches_returned_bytes(tmp_path: Path) -> None:
    body = {
        "data": [{
            "b64_json": base64.b64encode(PNG_BYTES).decode("ascii"),
            "media_type": "image/png",
        }]
    }
    provider = OpenRouterImageProvider(api_key="test")
    with patch.dict("os.environ", {"UCOS_IMAGE_OUTPUT_DIR": str(tmp_path)}):
        with patch(
            "layers.layer05_image.modules.image_provider.openrouter_image_provider.urllib.request.urlopen",
            return_value=FakeResponse(body),
        ):
            result = provider.generate("photo", size="512x512")

    assert result.metadata["sha256"] == hashlib.sha256(result.image_data).hexdigest()
    assert Path(result.image_url).read_bytes() == result.image_data


def test_storage_failure_propagates_and_cleans_temp_file(tmp_path: Path) -> None:
    body = {
        "data": [{
            "b64_json": base64.b64encode(PNG_BYTES).decode("ascii"),
            "media_type": "image/png",
        }]
    }
    provider = OpenRouterImageProvider(api_key="test")
    with patch.dict("os.environ", {"UCOS_IMAGE_OUTPUT_DIR": str(tmp_path)}):
        with patch(
            "layers.layer05_image.modules.image_provider.openrouter_image_provider.urllib.request.urlopen",
            return_value=FakeResponse(body),
        ):
            with patch(
                "layers.layer05_image.modules.image_provider.openrouter_image_provider.os.replace",
                side_effect=OSError("storage unavailable"),
            ):
                with pytest.raises(OSError, match="storage unavailable"):
                    provider.generate("photo")

    assert list(tmp_path.iterdir()) == []
