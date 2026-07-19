"""CancellationEngine — manage cancellation tokens for async operations."""
from __future__ import annotations
import time
import uuid
from typing import Any, Callable, Dict, List, Optional
from enum import Enum


class CancellationTokenState(str, Enum):
    ACTIVE = "active"; CANCELLED = "cancelled"


class CancellationToken:
    __slots__ = ("token_id", "state", "callbacks", "cancelled_at", "reason", "metadata")

    def __init__(self, token_id: Optional[str] = None) -> None:
        self.token_id = token_id or str(uuid.uuid4())[:12]
        self.state = CancellationTokenState.ACTIVE
        self.callbacks: List[Callable] = []
        self.cancelled_at: float = 0.0
        self.reason: str = ""
        self.metadata: Dict[str, Any] = {}

    def is_cancelled(self) -> bool:
        return self.state == CancellationTokenState.CANCELLED

    def register_callback(self, callback: Callable) -> None:
        self.callbacks.append(callback)

    def to_dict(self) -> Dict[str, Any]:
        return {"token_id": self.token_id, "state": self.state.value,
                "reason": self.reason}


class CancellationEngine:
    def __init__(self) -> None:
        self._tokens: Dict[str, CancellationToken] = {}

    def create_token(self, token_id: Optional[str] = None) -> CancellationToken:
        token = CancellationToken(token_id)
        self._tokens[token.token_id] = token
        return token

    def cancel(self, token_id: str, reason: str = "") -> bool:
        token = self._tokens.get(token_id)
        if token and token.state == CancellationTokenState.ACTIVE:
            token.state = CancellationTokenState.CANCELLED
            token.cancelled_at = time.time()
            token.reason = reason
            for cb in token.callbacks:
                try:
                    cb(token)
                except Exception:
                    pass
            return True
        return False

    def is_cancelled(self, token_id: str) -> bool:
        token = self._tokens.get(token_id)
        return token.is_cancelled() if token else True

    def get_token(self, token_id: str) -> Optional[CancellationToken]:
        return self._tokens.get(token_id)

    def list_tokens(self) -> List[Dict[str, Any]]:
        return [t.to_dict() for t in self._tokens.values()]

    def cleanup(self) -> int:
        cancelled = [t for t in self._tokens.values()
                     if t.state == CancellationTokenState.CANCELLED]
        for t in cancelled:
            del self._tokens[t.token_id]
        return len(cancelled)

    def count(self) -> int:
        return len(self._tokens)
