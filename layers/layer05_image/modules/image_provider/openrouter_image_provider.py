"""OpenRouter image provider for temporary Layer 5 image generation."""
from __future__ import annotations

import base64
import hashlib
import json
import os
import tempfile
import time
import urllib.error
import urllib.request
from typing import Any, Optional

from .image_provider import BaseImageProvider, ImageResponse


class OpenRouterImageProvider(BaseImageProvider):
    """Real image generation through OpenRouter's unified Image API."""

    API_URL = "https://openrouter.ai/api/v1/images"
    DEFAULT_MODEL = "bytedance-seed/seedream-4.5"

    def __init__(self, api_key: Optional[str] = None,
                 model: str = DEFAULT_MODEL) -> None:
        super().__init__(provider_name="openrouter_image", api_key=api_key or "")
        self._model = model
        self._timeout = 120

    def _get_api_key(self) -> str:
        return (self.api_key or os.environ.get("OPENROUTER_API_KEY", "")).strip()

    def is_configured(self) -> bool:
        return bool(self._get_api_key()) and bool(self._model.strip())

    def generate(self, prompt: str, size: str = "1024x1024",
                 **kwargs: Any) -> ImageResponse:
        if not prompt or not prompt.strip():
            raise ValueError("Image generation prompt must not be empty")
        if not self.is_configured():
            raise RuntimeError("OpenRouter image provider is not configured")

        payload = {
            "model": self._model,
            "prompt": prompt.strip(),
            "resolution": self._resolution(size),
            "aspect_ratio": self._aspect_ratio(size),
            "n": 1,
        }
        request = urllib.request.Request(
            self.API_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self._get_api_key()}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        start = time.monotonic()
        with self._counter_lock:
            self._call_count += 1
        try:
            with urllib.request.urlopen(request, timeout=self._timeout) as response:
                body = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code == 401:
                raise RuntimeError("OpenRouter authentication failed") from exc
            if exc.code == 402:
                raise RuntimeError("OpenRouter account has insufficient credits") from exc
            if exc.code == 429:
                raise RuntimeError("OpenRouter rate limit exceeded") from exc
            raise RuntimeError(f"OpenRouter HTTP request failed ({exc.code})") from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise RuntimeError("OpenRouter transport failed") from exc
        except json.JSONDecodeError as exc:
            raise RuntimeError("OpenRouter returned invalid JSON") from exc

        images = body.get("data")
        if not isinstance(images, list) or not images or not isinstance(images[0], dict):
            raise RuntimeError("OpenRouter returned no image data")
        encoded = images[0].get("b64_json")
        if not isinstance(encoded, str) or not encoded:
            raise RuntimeError("OpenRouter returned no base64 image data")
        try:
            image_bytes = base64.b64decode(encoded, validate=True)
        except (ValueError, TypeError) as exc:
            raise RuntimeError("OpenRouter returned invalid image encoding") from exc
        if not image_bytes:
            raise RuntimeError("OpenRouter returned empty image bytes")

        mime_type = str(images[0].get("media_type") or "").strip().lower()
        if not mime_type.startswith("image/"):
            raise RuntimeError("OpenRouter returned a non-image media type")
        if not image_bytes.startswith((b"\x89PNG\r\n\x1a\n", b"\xff\xd8\xff", b"RIFF")):
            raise RuntimeError("OpenRouter returned bytes that do not match a supported image signature")

        digest = hashlib.sha256(image_bytes).hexdigest()
        result = ImageResponse()
        result.image_data = image_bytes
        result.provider = "openrouter"
        result.model = self._model
        result.latency_ms = (time.monotonic() - start) * 1000
        result.metadata = {
            "mime_type": mime_type,
            "sha256": digest,
            "cost": (body.get("usage") or {}).get("cost"),
        }
        result.image_url = self._persist_image(image_bytes, mime_type)
        return result

    @staticmethod
    def _parse_size(size: str) -> tuple[int, int]:
        try:
            width, height = (int(part) for part in size.lower().split("x", 1))
        except (ValueError, TypeError):
            raise ValueError("Image size must use WIDTHxHEIGHT notation") from None
        if not (256 <= width <= 4096 and 256 <= height <= 4096):
            raise ValueError("Image dimensions must be between 256 and 4096 pixels")
        return width, height

    @classmethod
    def _aspect_ratio(cls, size: str) -> str:
        width, height = cls._parse_size(size)
        choices = {
            "1:1": 1.0, "2:3": 2 / 3, "3:2": 1.5, "3:4": 0.75,
            "4:3": 4 / 3, "4:5": 0.8, "5:4": 1.25, "9:16": 9 / 16,
            "16:9": 16 / 9, "21:9": 21 / 9,
        }
        ratio = width / height
        return min(choices, key=lambda key: abs(choices[key] - ratio))

    @classmethod
    def _resolution(cls, size: str) -> str:
        width, height = cls._parse_size(size)
        pixels = width * height
        if pixels <= 1024 * 1024:
            return "1K"
        if pixels <= 2048 * 2048:
            return "2K"
        return "4K"

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
        }.get(mime_type.lower(), ".bin")
        digest = hashlib.sha256(image_bytes).hexdigest()[:24]
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
