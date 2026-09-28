"""Production-boundary tests for the Layer 5 Puter.js image provider."""
from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from layers.layer05_image.modules.image_provider.puter_image_provider import (
    PuterImageProvider,
)

PNG_BYTES = b"\x89PNG\r\n\x1a\nreal-puter-image"


def test_provider_fails_closed_without_auth_token() -> None:
    provider = PuterImageProvider(auth_token=None)
    with patch.dict("os.environ", {}, clear=True):
        provider._auth_token = ""
        assert provider.is_configured() is False
        with pytest.raises(RuntimeError, match="not configured"):
            provider.generate("a product photo")


def test_invalid_size_is_rejected_before_process_start() -> None:
    provider = PuterImageProvider(auth_token="token")
    with patch.object(provider, "is_configured", return_value=True):
        with patch("subprocess.run") as run:
            with pytest.raises(ValueError, match="WIDTHxHEIGHT"):
                provider.generate("photo", size="bad")
    run.assert_not_called()


def test_real_response_bytes_are_persisted_and_hashed(tmp_path: Path) -> None:
    payload = {
        "ok": True,
        "mime_type": "image/png",
        "bytes_base64": base64.b64encode(PNG_BYTES).decode("ascii"),
        "source": "data_uri",
    }

    class Completed:
        returncode = 0
        stdout = json.dumps(payload) + "\n"
        stderr = ""

    provider = PuterImageProvider(auth_token="real-token")
    with patch.dict("os.environ", {"UCOS_IMAGE_OUTPUT_DIR": str(tmp_path)}):
        with patch("layers.layer05_image.modules.image_provider.puter_image_provider.subprocess.run", return_value=Completed()):
            result = provider.generate("photo", size="512x512")

    assert result.image_data == PNG_BYTES
    assert result.provider == "puter"
    assert result.metadata["sha256"] == hashlib.sha256(PNG_BYTES).hexdigest()
    assert Path(result.image_url).read_bytes() == PNG_BYTES


def test_bridge_error_is_fail_closed() -> None:
    class Completed:
        returncode = 1
        stdout = json.dumps(
            {"ok": False, "code": "insufficient_funds", "message": "balance too low"}
        )
        stderr = ""

    provider = PuterImageProvider(auth_token="real-token")
    with patch.object(provider, "is_configured", return_value=True):
        with patch("layers.layer05_image.modules.image_provider.puter_image_provider.subprocess.run", return_value=Completed()):
            with pytest.raises(RuntimeError, match="insufficient_funds"):
                provider.generate("photo")


def test_bridge_timeout_is_propagated() -> None:
    provider = PuterImageProvider(auth_token="real-token")
    with patch.object(provider, "is_configured", return_value=True):
        with patch(
            "layers.layer05_image.modules.image_provider.puter_image_provider.subprocess.run",
            side_effect=__import__("subprocess").TimeoutExpired("node", 120),
        ):
            with pytest.raises(RuntimeError, match="timed out"):
                provider.generate("photo")


def test_persisted_hash_matches_returned_bytes(tmp_path: Path) -> None:
    payload = {
        "ok": True,
        "mime_type": "image/jpeg",
        "bytes_base64": base64.b64encode(b"\xff\xd8\xffreal-jpeg").decode("ascii"),
    }

    class Completed:
        returncode = 0
        stdout = json.dumps(payload)
        stderr = ""

    provider = PuterImageProvider(auth_token="token")
    with patch.dict("os.environ", {"UCOS_IMAGE_OUTPUT_DIR": str(tmp_path)}):
        with patch("layers.layer05_image.modules.image_provider.puter_image_provider.subprocess.run", return_value=Completed()):
            result = provider.generate("photo", size="512x512")

    assert result.metadata["sha256"] == hashlib.sha256(result.image_data).hexdigest()


def test_node_runtime_unavailable_fails_closed() -> None:
    provider = PuterImageProvider(auth_token="real-token")
    with patch.object(provider, "is_configured", return_value=True):
        with patch(
            "layers.layer05_image.modules.image_provider.puter_image_provider.subprocess.run",
            side_effect=OSError("node missing"),
        ):
            with pytest.raises(RuntimeError, match="runtime is unavailable"):
                provider.generate("photo")
