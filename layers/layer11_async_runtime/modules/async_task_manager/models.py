"""Canonical async task model and lifecycle state."""
from __future__ import annotations

import time
import uuid
from enum import Enum
from typing import Any, Dict, List, Optional


class TaskState(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class AsyncTask:
    __slots__ = (
        "task_id",
        "name",
        "state",
        "priority",
        "result",
        "error",
        "dependencies",
        "created_at",
        "started_at",
        "completed_at",
        "metadata",
        "retries",
        "max_retries",
        "timeout",
    )

    def __init__(self, name: str = "", priority: int = 1) -> None:
        if priority < 0:
            raise ValueError("priority must be >= 0")
        self.task_id = f"task_{uuid.uuid4().hex}"
        self.name = name
        self.state = TaskState.PENDING
        self.priority = priority
        self.result: Any = None
        self.error: Optional[str] = None
        self.dependencies: List[str] = []
        self.created_at = time.time()
        self.started_at = None
        self.completed_at = None
        self.metadata: Dict[str, Any] = {}
        self.retries = 0
        self.max_retries = 3
        self.timeout = 300.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "name": self.name,
            "state": self.state.value,
            "priority": self.priority,
        }
