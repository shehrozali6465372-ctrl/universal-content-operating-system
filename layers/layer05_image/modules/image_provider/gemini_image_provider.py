"""GeminiImageProvider — Real image generation via Gemini API.

Uses Gemini's generateContent with image output capabilities.
Falls back to mock when API keys not available.

Architecture:
    ImageOrchestrator → GeminiImageProvider → KeyManager → Gemini API

Supports:
- Text-to-image prompts
- Image description enhancement
- Batch generation
- Style control
"""
from __future__ import annotations
import json
import os
import time
import urllib.request
import urllib.error
from typing import Any, Dict, List, Optional

from .image_provider import BaseImageProvider, ImageResponse


class GeminiImageProvider(BaseImageProvider):
    """Real Gemini-based image generation provider.

    Uses Gemini's multimodal capabilities to generate image descriptions
    and prompts that can be used with image generation APIs.

    When Gemini Imagen API is available:
    - Sends prompt to generateContent
    - Receives image data in response
    - Returns ImageResponse with image_data

    When API not available:
    - Returns enhanced prompt with style guidance
    - Logs the prompt for manual generation
    """

    GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta"
    SUPPORTED_MODELS = ["gemini-2.0-flash", "gemini-1.5-pro", "gemini-1.5-flash"]

    def __init__(self, api_key: str = "", model: str = "gemini-2.0-flash") -> None:
        super().__init__(provider_name="gemini_image", api_key=api_key)
        self._model = model
        self._timeout = 60
        self._history: List[Dict[str, Any]] = []

    def generate(self, prompt: str, size: str = "1024x1024",
                 style: str = "photorealistic", **kwargs: Any) -> ImageResponse:
        """Generate image via Gemini API.

        Strategy:
        1. Enhance prompt with style and size details
        2. Send to Gemini generateContent
        3. Parse response for image data or enhanced prompt
        4. Return ImageResponse
        """
        start = time.time()
        self._call_count += 1

        # Build enhanced prompt
        enhanced_prompt = self._enhance_prompt(prompt, size, style, **kwargs)

        # Try real API call
        api_key = self._get_api_key()
        if api_key:
            result = self._real_generate(enhanced_prompt, api_key, size)
            if result is not None:
                result.latency_ms = (time.time() - start) * 1000
                self._history.append({
                    "prompt": prompt[:100],
                    "size": size,
                    "style": style,
                    "status": "success",
                    "latency_ms": result.latency_ms,
                    "time": time.time(),
                })
                return result

        # Fallback: return enhanced prompt for manual/external generation
        result = ImageResponse()
        result.image_url = ""
        result.provider = "gemini_image_prompt"
        result.model = self._model
        result.revised_prompt = enhanced_prompt
        result.metadata = {
            "enhanced": True,
            "size": size,
            "style": style,
            "original_prompt": prompt[:200],
            "note": "Set GEMINI_API_KEY_1 for actual image generation",
        }
        result.latency_ms = (time.time() - start) * 1000
        self._history.append({
            "prompt": prompt[:100],
            "size": size,
            "style": style,
            "status": "prompt_enhanced",
            "latency_ms": result.latency_ms,
            "time": time.time(),
        })
        return result

    def generate_with_reference(self, prompt: str, reference_url: str = "",
                                size: str = "1024x1024",
                                **kwargs: Any) -> ImageResponse:
        """Generate image with reference image guidance."""
        enhanced = f"{prompt}\nReference style: similar to {reference_url}" if reference_url else prompt
        return self.generate(enhanced, size=size, **kwargs)

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
        """Real Gemini API call for image generation.

        Uses generateContent with image generation config.
        """
        url = (
            f"{self.GEMINI_API_BASE}/models/{self._model}"
            f":generateContent?key={api_key}"
        )

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "responseModalities": ["TEXT", "IMAGE"],
                "temperature": 0.4,
            }
        }

        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                url, data=data,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                body = json.loads(resp.read().decode("utf-8"))

            candidates = body.get("candidates", [])
            if not candidates:
                return None

            parts = candidates[0].get("content", {}).get("parts", [])

            result = ImageResponse()
            result.provider = "gemini"
            result.model = self._model

            # Check for image data in response
            for part in parts:
                if "inlineData" in part:
                    mime_type = part["inlineData"].get("mimeType", "")
                    data_b64 = part["inlineData"].get("data", "")
                    if data_b64:
                        import base64
                        result.image_data = base64.b64decode(data_b64)
                        result.metadata["mime_type"] = mime_type
                        result.metadata["has_image"] = True
                        # Save to file
                        ext = "png" if "png" in mime_type else "jpg"
                        filename = f"generated_{int(time.time())}.{ext}"
                        output_dir = os.path.join("output", "images")
                        os.makedirs(output_dir, exist_ok=True)
                        filepath = os.path.join(output_dir, filename)
                        with open(filepath, "wb") as f:
                            f.write(result.image_data)
                        result.image_url = filepath
                        break
                elif "text" in part:
                    result.revised_prompt = part["text"]

            # Save usage metadata
            usage = body.get("usageMetadata", {})
            result.metadata["tokens"] = usage.get("totalTokenCount", 0)

            return result

        except urllib.error.HTTPError as exc:
            if exc.code == 429:
                # Rate limited — log but don't crash
                pass
            return None
        except (urllib.error.URLError, TimeoutError, OSError):
            return None
        except (json.JSONDecodeError, KeyError, IndexError):
            return None

    def _get_api_key(self) -> str:
        """Get Gemini API key from environment."""
        if self.api_key:
            return self.api_key
        return os.environ.get("GEMINI_API_KEY_1", "")

    def _parse_size(self, size: str) -> tuple:
        """Parse size string like '1024x1024' to (width, height)."""
        try:
            parts = size.split("x")
            return (int(parts[0]), int(parts[1]))
        except (ValueError, IndexError):
            return (1024, 1024)

    def is_configured(self) -> bool:
        """Check if Gemini API key is available."""
        return bool(self._get_api_key())

    def get_stats(self) -> Dict[str, Any]:
        """Get provider statistics."""
        return {
            "provider": "gemini_image",
            "model": self._model,
            "total_calls": self._call_count,
            "is_configured": self.is_configured(),
            "history_size": len(self._history),
        }

    def get_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        return self._history[-limit:]
