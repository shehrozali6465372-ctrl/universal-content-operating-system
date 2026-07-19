"""AIResponse — encapsulate AI processing responses."""
from __future__ import annotations
from typing import Any, Dict

class AIResponse:
    def __init__(self) -> None:
        self.content: str = ""; self.confidence: float = 0.0
        self.metadata: Dict[str, Any] = {}; self.latency_ms: float = 0.0
        self.model: str = ""; self.provider: str = ""
        self.success: bool = True; self.error: str = ""
    def to_dict(self) -> Dict[str, Any]:
        return {"content": self.content[:200], "confidence": round(self.confidence, 4),
                "success": self.success, "model": self.model, "latency_ms": round(self.latency_ms, 2)}
