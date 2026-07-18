"""RuntimeContext — Execution context for runtime operations."""
from __future__ import annotations
import time
from typing import Any, Dict, Optional


class RuntimeContext:
    """Context for a runtime execution."""

    __slots__ = ("context_id", "operation", "user_id", "session_id",
                 "metadata", "created_at", "timeout")

    def __init__(self, operation: str = "") -> None:
        self.context_id: str = f"rctx_{int(time.time() * 1000)}"
        self.operation = operation
        self.user_id: Optional[str] = None
        self.session_id: Optional[str] = None
        self.metadata: Dict[str, Any] = {}
        self.created_at: float = time.time()
        self.timeout: float = 300.0

    def is_expired(self) -> bool:
        return (time.time() - self.created_at) > self.timeout

    def elapsed(self) -> float:
        return round(time.time() - self.created_at, 3)

    def to_dict(self) -> Dict[str, Any]:
        return {"context_id": self.context_id, "operation": self.operation,
                "elapsed": self.elapsed(), "timeout": self.timeout}
