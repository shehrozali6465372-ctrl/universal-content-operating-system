"""Data models for AI Orchestrator."""
from __future__ import annotations
import uuid
import time
from typing import Any, Dict, List
from dataclasses import dataclass, field
from enum import Enum

class TaskStatus(str, Enum):
    PENDING = "pending"; RUNNING = "running"; COMPLETED = "completed"
    FAILED = "failed"; CANCELLED = "cancelled"; RETRYING = "retrying"

class PipelineStatus(str, Enum):
    CREATED = "created"; RUNNING = "running"; COMPLETED = "completed"
    FAILED = "failed"; PAUSED = "paused"

@dataclass
class Task:
    task_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""; status: TaskStatus = TaskStatus.PENDING
    priority: int = 5; input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Dict[str, Any] = field(default_factory=dict)
    error: str = ""; retries: int = 0; max_retries: int = 3
    created_at: float = field(default_factory=time.time)
    completed_at: float = 0.0
    def to_dict(self) -> Dict[str, Any]:
        return {"task_id": self.task_id, "name": self.name, "status": self.status.value,
                "priority": self.priority, "retries": self.retries}

@dataclass
class Pipeline:
    pipeline_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""; tasks: List[Task] = field(default_factory=list)
    status: PipelineStatus = PipelineStatus.CREATED
    created_at: float = field(default_factory=time.time)
    def to_dict(self) -> Dict[str, Any]:
        return {"pipeline_id": self.pipeline_id, "name": self.name,
                "status": self.status.value, "task_count": len(self.tasks)}
