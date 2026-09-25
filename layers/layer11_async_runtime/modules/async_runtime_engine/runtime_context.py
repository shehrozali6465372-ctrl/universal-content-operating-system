"""RuntimeContext — validated execution context for runtime operations."""
from __future__ import annotations

import time
import uuid
from typing import Any, Dict, Optional


class RuntimeContext:
    """Immutable identity with monotonic elapsed-time accounting."""

    __slots__ = (
        "context_id", "operation", "user_id", "session_id",
        "metadata", "created_at", "_created_mono", "timeout",
    )

    def __init__(self, operation: str = "") -> None:
        if not isinstance(operation, str):
            raise TypeError("operation must be a string")
        self.context_id = f"rctx_{uuid.uuid4().hex}"
        self.operation = operation
        self.user_id: Optional[str] = None
        self.session_id: Optional[str] = None
        self.metadata: Dict[str, Any] = {}
        self.created_at = time.time()
        self._created_mono = time.monotonic()
        self.timeout = 300.0

    def is_expired(self) -> bool:
        if self.timeout <= 0:
            return True
        return time.monotonic() - self._created_mono > self.timeout

    def elapsed(self) -> float:
        return round(max(0.0, time.monotonic() - self._created_mono), 3)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "context_id": self.context_id,
            "operation": self.operation,
            "elapsed": self.elapsed(),
            "timeout": self.timeout,
        }
