"""Workflow Stage — Single execution stage within a workflow."""
from __future__ import annotations
import itertools
import time
from typing import Any, Dict, Optional

_WS_COUNTER = itertools.count(1)


class WorkflowStage:
    """Represents a single stage in a workflow."""

    __slots__ = ("stage_id", "layer", "module", "status", "order",
                 "result", "error", "retry_count", "max_retries",
                 "started_at", "completed_at", "duration_ms", "metadata")

    def __init__(self, layer: str = "", order: int = 0) -> None:
        self.stage_id: str = f"stage_{next(_WS_COUNTER)}"
        self.layer = layer
        self.module: str = ""
        self.status: str = "pending"
        self.order = order
        self.result: Any = None
        self.error: Optional[str] = None
        self.retry_count: int = 0
        self.max_retries: int = 3
        self.started_at: float = 0.0
        self.completed_at: float = 0.0
        self.duration_ms: float = 0.0
        self.metadata: Dict[str, Any] = {}

    def start(self) -> None:
        self.status = "running"
        self.started_at = time.time()

    def finish(self, result: Any = None) -> None:
        self.status = "completed"
        self.result = result
        self.completed_at = time.time()
        self.duration_ms = (self.completed_at - self.started_at) * 1000

    def fail(self, error: str = "") -> None:
        self.status = "failed"
        self.error = error
        self.completed_at = time.time()
        self.duration_ms = (self.completed_at - self.started_at) * 1000

    def reset(self) -> None:
        self.status = "pending"
        self.result = None
        self.error = None
        self.started_at = 0.0
        self.completed_at = 0.0
        self.duration_ms = 0.0

    def can_retry(self) -> bool:
        return self.status == "failed" and self.retry_count < self.max_retries

    def retry(self) -> bool:
        if self.can_retry():
            self.retry_count += 1
            self.reset()
            return True
        return False

    @property
    def is_terminal(self) -> bool:
        return self.status in ("completed", "failed", "cancelled")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage_id": self.stage_id,
            "layer": self.layer,
            "status": self.status,
            "retry_count": self.retry_count,
            "duration_ms": round(self.duration_ms, 1),
            "error": self.error,
        }
