"""Pipeline Context — Shared context passed through pipeline stages."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional


class PipelineContext:
    """Shared context for pipeline execution."""

    def __init__(self, platform: str = "", content: str = "") -> None:
        self.request_id: str = f"ctx_{int(time.time() * 1000) % 100000}"
        self.platform = platform
        self.content = content
        self.content_type: str = "post"
        self.media_paths: List[str] = []
        self.scheduled_time: Optional[float] = None
        self.metadata: Dict[str, Any] = {}
        self.stage_results: Dict[str, Any] = {}
        self.errors: List[str] = []
        self.created_at: float = time.time()

    def set_result(self, stage_name: str, result: Any) -> None:
        self.stage_results[stage_name] = result

    def get_result(self, stage_name: str) -> Any:
        return self.stage_results.get(stage_name)

    def add_error(self, error: str) -> None:
        self.errors.append(error[:500])

    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "platform": self.platform,
            "content_type": self.content_type,
            "content_length": len(self.content),
            "media_count": len(self.media_paths),
            "stage_count": len(self.stage_results),
            "error_count": len(self.errors),
            "created_at": self.created_at,
        }
