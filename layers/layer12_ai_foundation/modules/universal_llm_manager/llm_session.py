"""LLMSession — Session management for conversations."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional

class LLMSession:
    __slots__ = ("session_id", "user_id", "model", "provider", "context",
                 "total_tokens_used", "total_cost", "created_at", "last_active")

    def __init__(self, user_id: str = "") -> None:
        self.session_id: str = f"sess_{int(time.time()*1000)}"
        self.user_id = user_id
        self.model: str = ""
        self.provider: str = ""
        self.context: Dict[str, Any] = {}
        self.total_tokens_used: int = 0
        self.total_cost: float = 0.0
        self.created_at: float = time.time()
        self.last_active: float = time.time()

    def record_usage(self, tokens: int, cost: float) -> None:
        self.total_tokens_used += tokens
        self.total_cost += cost
        self.last_active = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {"session_id": self.session_id, "user_id": self.user_id,
                "tokens_used": self.total_tokens_used, "cost": round(self.total_cost, 4)}
