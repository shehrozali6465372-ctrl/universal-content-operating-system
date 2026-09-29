"""Puter.js-backed real image provider for Layer 5."""
from __future__ import annotations

import base64
import hashlib
import json
import os
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any, Optional

from .image_provider import BaseImageProvider, ImageResponse


class PuterImageProvider(BaseImageProvider):
    """Generate real images through the official Puter.js Node.js SDK.

    Backend/CI execution uses a real Puter auth token. Test-mode/synthetic
    responses are rejected so they cannot cross the production boundary.
    """

    DEFAULT_MODEL = ""
    DEFAULT_TIMEOUT_SECONDS = 120
    BRIDGE_PATH = (
        Path(__file__).resolve().parents[4] / "scripts" / "puter_image_provider.cjs"
    )

    def __init__(
        self,
        auth_token: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        node_binary: str = "node",
    ) -> None:
        super().__init__(provider_name="puter_image", api_key="")
        self._auth_token = auth_token or os.environ.get("PUTER_AUTH_TOKEN", "")
        self._model = model
        self._node_binary = node_binary
        self._timeout = int(
            os.environ.get(
                "PUTER_IMAGE_TIMEOUT_SECONDS", self.DEFAULT_TIMEOUT_SECONDS
            )
        )

    def _get_auth_token(self) -> str:
        return self._auth_token.strip()

    def is_configured(self) -> bool:
        return bool(self._get_auth_token()) and self.BRIDGE_PATH.is_file()

    def generate(
        self, prompt: str, size: str = "1024x1024", **kwargs: Any
    ) -> ImageResponse:
        if not prompt or not prompt.strip():
            raise ValueError("Image generation prompt must not be empty")
        if bool(kwargs.get("test_mode", False)):
            raise RuntimeError(
                "Puter test_mode is forbidden at the production image boundary"
            )
        if not self.is_configured():
            raise RuntimeError("Puter image provider is not configured")

        width, height = self._parse_size(size)
        request = {
            "prompt": prompt.strip(),
            "model": self._model.strip() or None,
            "provider": str(kwargs.get("provider") or "").strip() or None,
            "ratio": {"w": width, "h": height},
            "test_mode": False,
        }

        start = time.monotonic()
        with self._counter_lock:
            self._call_count += 1

        env = os.environ.copy()
        env["PUTER_AUTH_TOKEN"] = self._get_auth_token()
        try:
            completed = subprocess.run(
                [self._node_binary, str(self.BRIDGE_PATH)],
                input=json.dumps(request),
                text=True,
                capture_output=True,
                timeout=self._timeout,
                check=False,
                env=env,
            )
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError("Puter image generation timed out") from exc
        except OSError as exc:
            raise RuntimeError("Puter Node.js runtime is unavailable") from exc

        payload = self._decode_bridge_output(completed.stdout)
        if completed.returncode != 0 or not payload.get("ok"):
            code = str(payload.get("code") or "upstream_failed")
            message = str(
                payload.get("message")
                or completed.stderr.strip()
                or "Puter generation failed"
            )
            raise RuntimeError(f"Puter {code}: {message}")

        encoded = payload.get("bytes_base64")
        if not isinstance(encoded, str) or not encoded:
            raise RuntimeError("Puter returned no image bytes")
        try:
            image_bytes = base64.b64decode(encoded, validate=True)
        except (ValueError, TypeError) as exc:
            raise RuntimeError("Puter returned invalid image encoding") from exc
        if not image_bytes:
            raise RuntimeError("Puter returned empty image bytes")

        mime_type = str(payload.get("mime_type") or "").lower().strip()
        if not mime_type.startswith("image/"):
            raise RuntimeError("Puter returned a non-image media type")
        if not self._image_signature_matches_mime(image_bytes, mime_type):
            raise RuntimeError(
                "Puter returned bytes that do not match the declared image MIME type"
            )

        digest = hashlib.sha256(image_bytes).hexdigest()
        result = ImageResponse()
        result.image_data = image_bytes
        result.provider = "puter"
        result.model = self._model or "puter-default"
        result.latency_ms = (time.monotonic() - start) * 1000
        result.metadata = {
            "mime_type": mime_type,
            "sha256": digest,
            "source": payload.get("source", "unknown"),
            "auth_mode": "puter_auth_token",
            "production": True,
        }
        result.image_url = self._persist_image(image_bytes, mime_type)
        return result

    @staticmethod
    def _image_signature_matches_mime(image_bytes: bytes, mime_type: str) -> bool:
        """Validate that the declared MIME type matches the returned magic bytes."""
        signatures = {
            "image/png": (bytes.fromhex("89504e470d0a1a0a"),),
            "image/jpeg": (bytes.fromhex("ffd8ff"),),
            "image/webp": (b"RIFF",),
            "image/gif": (b"GIF8",),
        }
        expected = signatures.get(mime_type.lower().strip())
        return bool(expected and image_bytes.startswith(expected))

    @staticmethod
    def _decode_bridge_output(stdout: str) -> dict[str, Any]:
        lines = [line.strip() for line in stdout.splitlines() if line.strip()]
        if not lines:
            return {}
        try:
            payload = json.loads(lines[-1])
        except json.JSONDecodeError as exc:
            raise RuntimeError("Puter bridge returned invalid JSON") from exc
        if not isinstance(payload, dict):
            raise RuntimeError("Puter bridge returned invalid response")
        return payload

    @staticmethod
    def _parse_size(size: str) -> tuple[int, int]:
        try:
            width, height = (int(part) for part in size.lower().split("x", 1))
        except (ValueError, TypeError):
            raise ValueError("Image size must use WIDTHxHEIGHT notation") from None
        if not (256 <= width <= 4096 and 256 <= height <= 4096):
            raise ValueError("Image dimensions must be between 256 and 4096 pixels")
        return width, height

    @staticmethod
    def _persist_image(image_bytes: bytes, mime_type: str) -> str:
        output_dir = os.environ.get(
            "UCOS_IMAGE_OUTPUT_DIR", os.path.join("output", "images")
        )
        os.makedirs(output_dir, exist_ok=True)
        extension = {
            "image/png": ".png",
            "image/jpeg": ".jpg",
            "image/webp": ".webp",
            "image/gif": ".gif",
        }.get(mime_type, ".bin")
        digest = hashlib.sha256(image_bytes).hexdigest()
        fd, temp_path = tempfile.mkstemp(
            prefix=".image-", suffix=extension, dir=output_dir
        )
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(image_bytes)
                handle.flush()
                os.fsync(handle.fileno())
            final_path = os.path.join(output_dir, f"{digest}{extension}")
            os.replace(temp_path, final_path)
            return final_path
        except Exception:
            try:
                os.unlink(temp_path)
            except OSError:
                pass
            raise
