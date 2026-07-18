"""LLMResponse — Unified AI response model."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional

class LLMResponse:
    __slots__ = ("response_id", "request_id", "content", "model", "provider",
                 "finish_reason", "usage", "latency_ms", "created_at",
                 "metadata", "quality_score")

    def __init__(self, content: str = "", model: str = "", provider: str = "") -> None:
        self.response_id: str = f"resp_{int(time.time()*1000)}"
        self.request_id: str = ""
        self.content = content
        self.model = model
        self.provider = provider
        self.finish_reason: str = "stop"
        self.usage: Dict[str, int] = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        self.latency_ms: float = 0.0
        self.created_at: float = time.time()
        self.metadata: Dict[str, Any] = {}
        self.quality_score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {"response_id": self.response_id, "model": self.model,
                "provider": self.provider, "content_length": len(self.content),
                "usage": self.usage, "latency_ms": round(self.latency_ms, 2)}

    @property
    def total_tokens(self) -> int:
        return self.usage.get("total_tokens", 0)
