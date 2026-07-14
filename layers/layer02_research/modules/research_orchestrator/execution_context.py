"""
Execution Context
Layer 2: Research Engine — Module 10

Tracks the state of a single research execution:
- Execution metadata
- Module progress
- Confidence accumulation
- Timing information
"""

from datetime import datetime, timezone
from typing import Any, Dict, List


class ExecutionContext:
    """Tracks the full context of a single research execution."""

    __slots__ = (
        "execution_id", "topic", "niche", "status",
        "started_at", "completed_at", "current_module",
        "completed_modules", "failed_modules", "skipped_modules",
        "module_results", "overall_confidence",
        "total_api_calls", "total_duration_sec",
        "checkpoints", "metadata",
    )

    STATUSES = [
        "created", "planned", "running", "paused",
        "resuming", "completed", "failed", "cancelled", "retrying",
    ]

    def __init__(self, execution_id: str, topic: str, niche: str = "general"):
        self.execution_id = execution_id
        self.topic = topic
        self.niche = niche
        self.status = "created"
        self.started_at = datetime.now(timezone.utc).isoformat()
        self.completed_at = ""
        self.current_module = ""
        self.completed_modules: List[str] = []
        self.failed_modules: List[str] = []
        self.skipped_modules: List[str] = []
        self.module_results: Dict[str, Any] = {}
        self.overall_confidence = 0.0
        self.total_api_calls = 0
        self.total_duration_sec = 0.0
        self.checkpoints: List[Dict] = []
        self.metadata: Dict[str, Any] = {}

    def start(self):
        self.status = "running"
        self.started_at = datetime.now(timezone.utc).isoformat()

    def pause(self):
        self.status = "paused"

    def resume(self):
        self.status = "resuming"

    def complete(self, confidence: float = 0.0):
        self.status = "completed"
        self.overall_confidence = confidence
        self.completed_at = datetime.now(timezone.utc).isoformat()

    def fail(self):
        self.status = "failed"
        self.completed_at = datetime.now(timezone.utc).isoformat()

    def cancel(self):
        self.status = "cancelled"
        self.completed_at = datetime.now(timezone.utc).isoformat()

    def set_current_module(self, module: str):
        self.current_module = module

    def complete_module(self, module: str, result: Any = None, confidence: float = 0.0):
        if module not in self.completed_modules:
            self.completed_modules.append(module)
        self.failed_modules = [m for m in self.failed_modules if m != module]
        if module in self.metadata:
            self.metadata[module] = confidence
        self.overall_confidence = confidence

    def fail_module(self, module: str):
        if module not in self.failed_modules:
            self.failed_modules.append(module)
        self.completed_modules = [m for m in self.completed_modules if m != module]

    def skip_module(self, module: str):
        if module not in self.skipped_modules:
            self.skipped_modules.append(module)

    def store_result(self, module: str, result: Any):
        self.module_results[module] = result

    def get_progress(self) -> float:
        total = len(self.completed_modules) + len(self.failed_modules) + len(self.skipped_modules)
        if total == 0:
            return 0.0
        done = len(self.completed_modules) + len(self.skipped_modules)
        return round(done / max(total, 1), 3)

    def to_dict(self) -> dict:
        return {
            "execution_id": self.execution_id,
            "topic": self.topic,
            "niche": self.niche,
            "status": self.status,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "current_module": self.current_module,
            "completed_modules": list(self.completed_modules),
            "failed_modules": list(self.failed_modules),
            "skipped_modules": list(self.skipped_modules),
            "overall_confidence": self.overall_confidence,
            "total_api_calls": self.total_api_calls,
            "total_duration_sec": self.total_duration_sec,
            "progress": self.get_progress(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ExecutionContext":
        ctx = cls(
            execution_id=data.get("execution_id", ""),
            topic=data.get("topic", ""),
            niche=data.get("niche", "general"),
        )
        ctx.status = data.get("status", "created")
        ctx.started_at = data.get("started_at", ctx.started_at)
        ctx.completed_at = data.get("completed_at", "")
        ctx.current_module = data.get("current_module", "")
        ctx.completed_modules = data.get("completed_modules", [])
        ctx.failed_modules = data.get("failed_modules", [])
        ctx.skipped_modules = data.get("skipped_modules", [])
        ctx.overall_confidence = data.get("overall_confidence", 0.0)
        ctx.total_api_calls = data.get("total_api_calls", 0)
        ctx.total_duration_sec = data.get("total_duration_sec", 0.0)
        ctx.metadata = data.get("metadata", {})
        return ctx
