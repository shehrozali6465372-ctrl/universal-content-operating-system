"""MultiModelRequest — request model for multi-model operations."""
from __future__ import annotations

import uuid
import time
from typing import Any, Dict, List, Optional


class MultiModelRequest:
    """Encapsulates a multi-model request."""

    def __init__(self, prompt: str, models: Optional[List[str]] = None,
                 task_type: str = "generation", **kwargs: Any) -> None:
        self.request_id = str(uuid.uuid4())[:12]
        self.prompt = prompt
        self.models = models or ["gpt-4o", "claude-sonnet-4-20250514", "gemini-2.0-flash"]
        self.task_type = task_type
        self.config: Dict[str, Any] = kwargs
        self.created_at = time.time()
        self.metadata: Dict[str, Any] = {}

    def set(self, key: str, value: Any) -> None:
        self.metadata[key] = value

    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id, "prompt": self.prompt[:200],
            "models": self.models, "task_type": self.task_type,
            "config": self.config, "metadata": self.metadata,
        }
