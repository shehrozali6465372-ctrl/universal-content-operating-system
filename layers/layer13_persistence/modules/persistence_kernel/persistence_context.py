"""persistence_context.py — Persistence execution context."""
from __future__ import annotations
import time
from typing import Any, Dict


class PersistenceContext:
    """Tracks execution context for persistence operations."""

    __slots__ = ("context_id", "user_id", "session_id", "transaction_id",
                 "operation", "started_at", "metadata", "trace")

    _counter = 0

    def __init__(self, user_id: str = "", session_id: str = "",
                 operation: str = "") -> None:
        PersistenceContext._counter += 1
        self.context_id: int = PersistenceContext._counter
        self.user_id = user_id
        self.session_id = session_id
        self.transaction_id: str = ""
        self.operation = operation
        self.started_at: float = time.time()
        self.metadata: Dict[str, Any] = {}
        self.trace: list = []

    def add_trace(self, step: str, details: Dict[str, Any] = None) -> None:
        self.trace.append({"step": step, "time": time.time(), "details": details or {}})

    def set_transaction(self, transaction_id: str) -> None:
        self.transaction_id = transaction_id

    def elapsed_ms(self) -> float:
        return (time.time() - self.started_at) * 1000

    def to_dict(self) -> Dict[str, Any]:
        return {"context_id": self.context_id, "user_id": self.user_id,
                "session_id": self.session_id, "operation": self.operation,
                "trace_count": len(self.trace), "elapsed_ms": self.elapsed_ms()}
