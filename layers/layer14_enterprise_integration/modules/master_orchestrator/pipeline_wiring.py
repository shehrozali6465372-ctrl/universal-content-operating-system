"""PipelineWiring — wires all layers into a working content pipeline.

    User Request
        │
        ▼
    Layer 14 — IntegrationKernel
        │
        ▼
    Layer 12 — ModelRouter (KeyManager → GeminiProvider)
        │
        ▼
    Layer 4 — Writing (Draft Generator)
        │
        ▼
    Layer 6 — Quality (Quality Check)
        │
        ▼
    Response
"""
from __future__ import annotations
import os
import time
from typing import Any, Dict, Optional

from layers.layer12_ai_foundation.modules.model_router.key_manager import KeyManager
from layers.layer12_ai_foundation.modules.model_router.gemini_provider import GeminiProvider
from layers.layer12_ai_foundation.modules.model_router.prompt_builder import (
    PromptBuilder, PromptStyle
)


class ContentRequest:
    __slots__ = ("topic", "platform", "tone", "style", "include_image",
                 "max_length", "metadata")

    def __init__(self, topic: str, platform: str = "facebook",
                 tone: str = "professional", style: str = "educational",
                 include_image: bool = False, max_length: int = 1000) -> None:
        self.topic = topic
        self.platform = platform
        self.tone = tone
        self.style = style
        self.include_image = include_image
        self.max_length = max_length
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {"topic": self.topic, "platform": self.platform,
                "tone": self.tone, "style": self.style,
                "include_image": self.include_image}


class ContentResponse:
    __slots__ = ("text", "image_prompt", "quality_score", "published",
                 "stats", "metadata")

    def __init__(self) -> None:
        self.text = ""
        self.image_prompt = ""
        self.quality_score = 0.0
        self.published = False
        self.stats: Dict[str, Any] = {}
        self.metadata: Dict[str, Any] = {}


class PipelineWiring:
    """Wires all layers together into the content pipeline."""

    # GitHub Secret names (note: key 2 & 3 have no underscores)
    _GEMINI_KEYS = [
        ("GEMINI_API_KEY_1", "GEMINI_API_KEY_1"),
        ("GEMINI_API_KEY_2", "GEMINIAPIKEY2"),
        ("GEMINI_API_KEY_3", "GEMINIAPIKEY3"),
    ]

    def __init__(self) -> None:
        self._key_manager = KeyManager()
        for idx, (env_name, secret_name) in enumerate(self._GEMINI_KEYS, 1):
            key = os.environ.get(env_name) or os.environ.get(secret_name)
            if key:
                self._key_manager.register_key(f"k{idx}", key, "gemini")
        self._gemini = GeminiProvider(self._key_manager)
        self._prompt_builder = PromptBuilder()

    def execute(self, request: ContentRequest) -> ContentResponse:
        start = time.time()
        response = ContentResponse()

        prompt = self._prompt_builder.build(
            request.topic, PromptStyle.CHAIN_OF_THOUGHT,
            context={"platform": request.platform, "tone": request.tone}
        )
        user_msg = next(
            (m["content"] for m in prompt["messages"] if m["role"] == "user"), ""
        )
        result = self._gemini.generate(user_msg)
        response.text = result.get("content", "")

        if request.include_image:
            img_prompt = self._prompt_builder.build(
                f"A {request.tone} image for: {request.topic}", PromptStyle.DIRECT
            )
            response.image_prompt = " ".join(
                m["content"] for m in img_prompt["messages"]
            )

        if response.text:
            word_count = len(response.text.split())
            response.quality_score = min(10.0, word_count / 10)

        response.stats = {
            "execution_time_ms": round((time.time() - start) * 1000, 1),
            "content_length": len(response.text),
            "word_count": len(response.text.split()) if response.text else 0,
            "has_api_keys": self._key_manager.get_stats()["total_keys"] > 0,
        }
        return response

    def status(self) -> Dict[str, Any]:
        stats = self._key_manager.get_stats()
        return {"api_keys_configured": stats.get("total_keys", 0),
                "healthy_keys": stats.get("healthy", 0)}
