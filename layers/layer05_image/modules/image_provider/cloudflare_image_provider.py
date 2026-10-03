"""Cloudflare Workers AI image provider for Layer 5.

Uses the official Workers AI REST API and keeps provider-specific transport
inside the Layer 5 image-provider boundary.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Optional

from .image_provider import BaseImageProvider, ImageResponse


class CloudflareImageProvider(BaseImageProvider):
    """Generate and persist real images through Cloudflare Workers AI."""

    DEFAULT_MODEL = "@cf/bytedance/stable-diffusion-xl-lightning"
    DEFAULT_TIMEOUT_SECONDS = 180

    def __init__(
        self,
        api_token: Optional[str] = None,
        account_id: Optional[str] = None,
        model: Optional[str] = None,
    ) -> None:
        super().__init__(provider_name="cloudflare_workers_ai", api_key="")
        self._api_token = (
            api_token
            or os.environ.get("CLOUDFLARE_API_TOKEN")
            or os.environ.get("CF_API_TOKEN")
            or ""
        ).strip()
        self._account_id = (
            account_id
            or os.environ.get("CLOUDFLARE_ACCOUNT_ID")
            or os.environ.get("CF_ACCOUNT_ID")
            or ""
        ).strip()
        self._model = (
            model
            or os.environ.get("CLOUDFLARE_IMAGE_MODEL")
            or self.DEFAULT_MODEL
        ).strip()
        self._timeout = int(
            os.environ.get(
                "CLOUDFLARE_IMAGE_TIMEOUT_SECONDS",
                self.DEFAULT_TIMEOUT_SECONDS,
            )
        )

    def is_configured(self) -> bool:
        return bool(self._api_token and self._account_id and self._model)

    def generate(self, prompt: str, size: str = "1024x1024", **kwargs: Any) -> ImageResponse:
        if not prompt or not prompt.strip():
            raise ValueError("Image generation prompt must not be empty")
        if not self.is_configured():
            raise RuntimeError(
                "Cloudflare Workers AI image provider is not configured"
            )

        width, height = self._parse_size(size)
        payload: dict[str, Any] = {
            "prompt": prompt.strip(),
            "width": width,
            "height": height,
        }
        for key in ("negative_prompt", "num_steps", "guidance", "seed"):
            if key in kwargs and kwargs[key] is not None:
                payload[key] = kwargs[key]

        url = (
            f"https://api.cloudflare.com/client/v4/accounts/"
            f"{self._account_id}/ai/run/{self._model}"
        )
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            method="POST",
            headers={
                "Authorization": f"Bearer {self._api_token}",
                "Content-Type": "application/json",
            },
        )

        start = time.monotonic()
        with self._counter_lock:
            self._call_count += 1
        try:
            with urllib.request.urlopen(request, timeout=self._timeout) as response:
                body = response.read()
                content_type = str(response.headers.get("Content-Type") or "").lower()
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError) as exc:
            raise RuntimeError(
                f"Cloudflare Workers AI request failed: {type(exc).__name__}"
            ) from exc

        image_bytes = self._decode_image_response(body, content_type)
        if not image_bytes:
            raise RuntimeError("Cloudflare Workers AI returned empty image bytes")
        if not self._looks_like_image(image_bytes):
            raise RuntimeError("Cloudflare Workers AI returned non-image bytes")

        digest = hashlib.sha256(image_bytes).hexdigest()
        result = ImageResponse()
        result.image_data = image_bytes
        result.provider = "cloudflare_workers_ai"
        result.model = self._model
        result.latency_ms = (time.monotonic() - start) * 1000
        result.metadata = {
            "mime_type": "image/png",
            "sha256": digest,
            "account_id_configured": True,
            "production": True,
        }
        result.image_url = self._persist_image(image_bytes)
        return result

    @staticmethod
    def _decode_image_response(body: bytes, content_type: str) -> bytes:
        if body.startswith(b"\x89PNG\r\n\x1a\n") or body.startswith(b"\xff\xd8\xff"):
            return body
        try:
            decoded = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return body

        result = decoded.get("result") if isinstance(decoded, dict) else None
        if isinstance(result, str):
            try:
                return base64.b64decode(result, validate=True)
            except (ValueError, TypeError):
                return result.encode("utf-8")
        if isinstance(result, dict):
            for key in ("image", "image_b64", "bytes_base64"):
                value = result.get(key)
                if isinstance(value, str):
                    try:
                        return base64.b64decode(value, validate=True)
                    except (ValueError, TypeError):
                        continue
        return b""

    @staticmethod
    def _looks_like_image(data: bytes) -> bool:
        return (
            data.startswith(b"\x89PNG\r\n\x1a\n")
            or data.startswith(b"\xff\xd8\xff")
            or (data.startswith(b"RIFF") and data[8:12] == b"WEBP")
            or data.startswith(b"GIF8")
        )

    @staticmethod
    def _parse_size(size: str) -> tuple[int, int]:
        try:
            width, height = (int(part) for part in size.lower().split("x", 1))
        except (ValueError, TypeError):
            raise ValueError("Image size must use WIDTHxHEIGHT notation") from None
        if not (256 <= width <= 2048 and 256 <= height <= 2048):
            raise ValueError("Cloudflare image dimensions must be 256..2048 pixels")
        return width, height

    @staticmethod
    def _persist_image(image_bytes: bytes) -> str:
        output_dir = os.environ.get(
            "UCOS_IMAGE_OUTPUT_DIR", os.path.join("output", "images")
        )
        os.makedirs(output_dir, exist_ok=True)
        digest = hashlib.sha256(image_bytes).hexdigest()
        fd, temp_path = tempfile.mkstemp(
            prefix=".cloudflare-image-",
            suffix=".png",
            dir=output_dir,
        )
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(image_bytes)
                handle.flush()
                os.fsync(handle.fileno())
            final_path = os.path.join(output_dir, f"{digest}.png")
            os.replace(temp_path, final_path)
            return final_path
        except Exception:
            try:
                os.unlink(temp_path)
            except OSError:
                pass
            raise
