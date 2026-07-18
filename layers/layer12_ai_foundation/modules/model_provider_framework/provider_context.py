"""provider_context.py — Provider execution context."""
from __future__ import annotations
import time
import itertools
from typing import Any, Dict, Optional

_CTX_ID = itertools.count(1)


class ProviderContext:
    """Tracks the execution context for a provider call."""

    __slots__ = ("context_id", "provider", "model", "user_id", "session_id",
                 "created_at", "metadata", "trace")

    def __init__(self, provider: str, model: str, user_id: str = "",
                 session_id: str = "") -> None:
        self.context_id: int = next(_CTX_ID)
        self.provider = provider
        self.model = model
        self.user_id = user_id
        self.session_id = session_id
        self.created_at: float = time.time()
        self.metadata: Dict[str, Any] = {}
        self.trace: list = []

    def add_trace(self, event: str, details: Optional[Dict[str, Any]] = None) -> None:
        self.trace.append({"event": event, "time": time.time(), "details": details or {}})

    def to_dict(self) -> Dict[str, Any]:
        return {"context_id": self.context_id, "provider": self.provider,
                "model": self.model, "user_id": self.user_id,
                "created_at": self.created_at, "trace_count": len(self.trace)}
