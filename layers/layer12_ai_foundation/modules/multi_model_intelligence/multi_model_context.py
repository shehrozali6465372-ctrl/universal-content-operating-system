"""MultiModelContext — execution context for multi-model operations."""
from __future__ import annotations

import uuid
import time
from typing import Any, Dict, Optional


class MultiModelContext:
    """Tracks context during a multi-model operation."""

    def __init__(self, session_id: Optional[str] = None) -> None:
        self.session_id = session_id or str(uuid.uuid4())[:12]
        self.created_at = time.time()
        self.metadata: Dict[str, Any] = {}
        self.model_responses: Dict[str, Any] = {}
        self.results: Dict[str, Any] = {}
        self._stage_history: list = []

    def set(self, key: str, value: Any) -> None:
        self.metadata[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self.metadata.get(key, default)

    def add_response(self, model: str, response: Any) -> None:
        self.model_responses[model] = response

    def set_result(self, key: str, value: Any) -> None:
        self.results[key] = value

    def record_stage(self, stage: str, data: Any) -> None:
        self._stage_history.append({"stage": stage, "data": data, "time": time.time()})

    def get_stages(self) -> list:
        return list(self._stage_history)

    def to_dict(self) -> Dict[str, Any]:
        return {"session_id": self.session_id, "metadata": self.metadata,
                "model_count": len(self.model_responses), "result_keys": list(self.results.keys())}

    def clear(self) -> None:
        self.metadata.clear()
        self.model_responses.clear()
        self.results.clear()
        self._stage_history.clear()
