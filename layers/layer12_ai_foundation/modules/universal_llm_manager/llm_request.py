"""LLMRequest — Unified AI request model."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional

class LLMRequest:
    __slots__ = ("request_id", "prompt", "system_prompt", "model", "provider",
                 "temperature", "max_tokens", "top_p", "frequency_penalty",
                 "presence_penalty", "stop", "stream", "context", "metadata",
                 "created_at")

    def __init__(self, prompt: str = "", model: str = "", provider: str = "") -> None:
        self.request_id: str = f"req_{int(time.time()*1000)}"
        self.prompt = prompt
        self.system_prompt: str = ""
        self.model = model
        self.provider = provider
        self.temperature: float = 0.7
        self.max_tokens: int = 4096
        self.top_p: float = 1.0
        self.frequency_penalty: float = 0.0
        self.presence_penalty: float = 0.0
        self.stop: Optional[List[str]] = None
        self.stream: bool = False
        self.context: List[Dict[str, str]] = []
        self.metadata: Dict[str, Any] = {}
        self.created_at: float = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {"request_id": self.request_id, "prompt": self.prompt[:100],
                "model": self.model, "provider": self.provider}
