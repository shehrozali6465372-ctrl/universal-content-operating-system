"""GeminiImageProvider — Real image generation via Gemini API.

Uses Gemini's generateContent with image output capabilities.
Fails closed when API credentials or generation responses are unavailable.

Architecture:
    ImageOrchestrator → GeminiImageProvider → KeyManager → Gemini API

Supports:
- Text-to-image prompts
- Image description enhancement
- Batch generation
- Style control
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
from threading import RLock
from typing import Any, Dict, List, Optional, Tuple

from .image_provider import BaseImageProvider, ImageResponse


class GeminiImageProvider(BaseImageProvider):
    """Real Gemini-based image generation provider.

    Uses Gemini's multimodal capabilities to generate image descriptions
    and prompts that can be used with image generation APIs.

    When Gemini Imagen API is available:
    - Sends prompt to generateContent
    - Receives image data in response
    - Returns ImageResponse with image_data

    """

    GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1"
    SUPPORTED_MODELS = [
        "gemini-3.1-flash-image",
        "gemini-3-pro-image",
        "gemini-2.5-flash-image",
    ]

    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-3.1-flash-image") -> None:
        super().__init__(provider_name="gemini_image", api_key=api_key)
        self._model = model
        self._timeout = 60
        self._history: List[Dict[str, Any]] = []
        self._max_history = 1000
        self._history_lock = RLock()

    def generate(self, prompt: str, size: str = "1024x1024",
                 style: str = "photorealistic", **kwargs: Any) -> ImageResponse:
        """Generate a real image; never return a synthetic success."""
        if not prompt or not prompt.strip():
            raise ValueError("Image generation prompt must not be empty")
        api_key = self._get_api_key()
        if not api_key or self._model not in self.SUPPORTED_MODELS:
            raise RuntimeError("Gemini image provider is not configured")
        start = time.monotonic()
        with self._history_lock:
            self._call_count += 1
        enhanced_prompt = self._enhance_prompt(prompt, size, style, **kwargs)
        try:
            result = self._real_generate(enhanced_prompt, api_key, size)
        except Exception as exc:
            self._record_history({"status": "error", "error_type": type(exc).__name__,
                                  "latency_ms": (time.monotonic() - start) * 1000})
            raise RuntimeError("Gemini image generation failed") from exc
        if result is None or not result.image_data:
            raise RuntimeError("Gemini returned no image data")
        result.latency_ms = (time.monotonic() - start) * 1000
        self._record_history({"status": "success", "provider": result.provider,
                              "model": result.model, "bytes": len(result.image_data),
                              "sha256": result.metadata.get("sha256", ""),
                              "latency_ms": result.latency_ms})
        return result

    def generate_with_reference(self, prompt: str, reference_url: str = "",
                                size: str = "1024x1024",
                                **kwargs: Any) -> ImageResponse:
        """Generate with reference guidance only when a real reference is supplied.

        URL text is not a valid image reference input to Gemini. Until the provider
        accepts actual image bytes/parts, fail closed instead of pretending that a
        URL was supplied to the model as visual context.
        """
        if reference_url:
            raise NotImplementedError(
                "Gemini reference generation requires actual image bytes; URL-only reference input is unsupported"
            )
        return self.generate(prompt, size=size, **kwargs)

    def generate_batch(self, prompts: List[str], size: str = "1024x1024",
                       **kwargs: Any) -> List[ImageResponse]:
        """Generate multiple images sequentially."""
        results = []
        for prompt in prompts:
            results.append(self.generate(prompt, size=size, **kwargs))
            # Small delay between API calls to avoid rate limiting
            if len(prompts) > 1:
                time.sleep(0.5)
        return results

    def _enhance_prompt(self, prompt: str, size: str, style: str,
                        **kwargs: Any) -> str:
        """Enhance prompt with style and technical details."""
        width, height = self._parse_size(size)
        aspect_ratio = "square" if width == height else (
            "landscape" if width > height else "portrait"
        )

        enhanced = (
            f"Generate a {style} image.\n"
            f"Prompt: {prompt}\n"
            f"Dimensions: {width}x{height} ({aspect_ratio})\n"
            f"Quality: High resolution, professional, publication-ready\n"
            f"Style notes: Clean composition, balanced colors, "
            f"appropriate for social media sharing"
        )

        if kwargs.get("mood"):
            enhanced += f"\nMood: {kwargs['mood']}"
        if kwargs.get("color_scheme"):
            enhanced += f"\nColor palette: {kwargs['color_scheme']}"

        return enhanced

    def _real_generate(self, prompt: str, api_key: str,
                       size: str = "1024x1024") -> Optional[ImageResponse]:
        """Call Gemini's image-capable generateContent endpoint."""
        width, height = self._parse_size(size)
        url = f"{self.GEMINI_API_BASE}/models/{self._model}:generateContent"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "responseModalities": ["IMAGE"],
                "imageConfig": {
                    "aspectRatio": self._aspect_ratio(width, height),
                    "imageSize": self._image_size(width, height),
                },
            },
        }
        req = urllib.request.Request(
            url, data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "x-goog-api-key": api_key},
            method="POST")
        for attempt in range(4):
            try:
                with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                    body = json.loads(resp.read().decode("utf-8"))
                break
            except urllib.error.HTTPError as exc:
                if exc.code == 429 or 500 <= exc.code <= 599:
                    if attempt < 3:
                        time.sleep(2 ** attempt)
                        continue
                if exc.code == 429:
                    raise RuntimeError("Gemini rate limit exceeded") from exc
                if exc.code in (401, 403):
                    raise RuntimeError("Gemini authentication/authorization failed") from exc
                detail = ""
                try:
                    raw_error = exc.read().decode("utf-8", errors="replace")
                    parsed_error = json.loads(raw_error)
                    error_obj = parsed_error.get("error", {})
                    detail = str(error_obj.get("message") or error_obj.get("status") or "").strip()
                except (OSError, UnicodeError, json.JSONDecodeError):
                    detail = ""
                suffix = f": {detail}" if detail else ""
                raise RuntimeError(
                    f"Gemini HTTP request failed ({exc.code}){suffix}"
                ) from exc
            except (urllib.error.URLError, TimeoutError, OSError) as exc:
                if attempt < 3:
                    time.sleep(2 ** attempt)
                    continue
                raise RuntimeError("Gemini transport failed") from exc
            except json.JSONDecodeError as exc:
                raise RuntimeError("Gemini returned invalid JSON") from exc
        else:
            raise RuntimeError("Gemini request retry budget exhausted")
        result = ImageResponse()
        result.provider = "gemini"
        result.model = self._model
        for candidate in body.get("candidates", []):
            for part in candidate.get("content", {}).get("parts", []):
                inline = part.get("inlineData")
                if not inline or not inline.get("data"):
                    continue
                try:
                    image_bytes = base64.b64decode(inline["data"], validate=True)
                except (ValueError, TypeError) as exc:
                    raise RuntimeError("Gemini returned invalid image encoding") from exc
                mime_type = inline.get("mimeType", "")
                if not image_bytes or not mime_type.startswith("image/"):
                    continue
                result.image_data = image_bytes
                result.metadata["mime_type"] = mime_type
                result.metadata["sha256"] = hashlib.sha256(image_bytes).hexdigest()
                result.image_url = self._persist_image(image_bytes, mime_type)
                return result
        return None

    @staticmethod
    def _image_size(width: int, height: int) -> str:
        """Map requested canvas dimensions to Gemini's supported output tiers."""
        pixels = width * height
        if pixels <= 1024 * 1024:
            return "1K"
        if pixels <= 2048 * 2048:
            return "2K"
        return "4K"

    @staticmethod
    def _aspect_ratio(width: int, height: int) -> str:
        ratio = width / height
        choices = {"1:1": 1.0, "3:2": 1.5, "2:3": 2/3, "3:4": .75,
                   "4:3": 4/3, "4:5": .8, "5:4": 1.25, "9:16": 9/16,
                   "16:9": 16/9, "21:9": 21/9}
        return min(choices, key=lambda key: abs(choices[key] - ratio))

    def _persist_image(self, image_bytes: bytes, mime_type: str) -> str:
        output_dir = os.environ.get("UCOS_IMAGE_OUTPUT_DIR", os.path.join("output", "images"))
        os.makedirs(output_dir, exist_ok=True)
        ext = {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp"}.get(
            mime_type.lower(), ".bin")
        digest = hashlib.sha256(image_bytes).hexdigest()[:24]
        fd, temp_path = tempfile.mkstemp(prefix=".image-", suffix=ext, dir=output_dir)
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(image_bytes)
                handle.flush()
                os.fsync(handle.fileno())
            final_path = os.path.join(output_dir, f"{digest}{ext}")
            os.replace(temp_path, final_path)
            return final_path
        except Exception:
            try:
                os.unlink(temp_path)
            except OSError:
                pass
            raise

    def _get_api_key(self) -> str:
        """Get Gemini API key from environment."""
        if self.api_key is not None:
            return self.api_key.strip()
        for name in ("GEMINI_API_KEY_1", "GEMINI_API_KEY"):
            value = os.environ.get(name, "").strip()
            if value:
                return value
        return ""

    def _parse_size(self, size: str) -> Tuple[int, int]:
        """Parse and validate a WIDTHxHEIGHT size."""
        try:
            width, height = (int(part) for part in size.lower().split("x", 1))
        except (ValueError, TypeError):
            raise ValueError("Image size must use WIDTHxHEIGHT notation") from None
        if not (256 <= width <= 4096 and 256 <= height <= 4096):
            raise ValueError("Image dimensions must be between 256 and 4096 pixels")
        return width, height

    def is_configured(self) -> bool:
        """Check if Gemini API key is available."""
        return bool(self._get_api_key()) and self._model in self.SUPPORTED_MODELS

    def get_stats(self) -> Dict[str, Any]:
        """Get provider statistics."""
        with self._history_lock:
            total_calls = self._call_count
            history_size = len(self._history)
        return {
            "provider": "gemini_image",
            "model": self._model,
            "total_calls": total_calls,
            "is_configured": self.is_configured(),
            "history_size": history_size,
        }

    def _record_history(self, record: Dict[str, Any]) -> None:
        with self._history_lock:
            self._history.append(dict(record))
            if len(self._history) > self._max_history:
                del self._history[:-self._max_history]

    def get_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= self._max_history:
            raise ValueError(f"limit must be between 1 and {self._max_history}")
        with self._history_lock:
            return [dict(item) for item in self._history[-limit:]]
