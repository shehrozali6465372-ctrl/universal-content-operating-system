"""MappingHistory — Track all mapping changes for audit and rollback."""
from __future__ import annotations
import time
import uuid
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class MappingHistory:
    """Record of a mapping change with reason and AI confidence."""

    history_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    content_id: str = ""
    old_mapping: Dict[str, Any] = field(default_factory=dict)
    new_mapping: Dict[str, Any] = field(default_factory=dict)
    reason: str = ""
    ai_score: float = 0.0
    changed_by: str = "ai_engine"
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "history_id": self.history_id,
            "content_id": self.content_id,
            "reason": self.reason,
            "ai_score": round(self.ai_score, 2),
            "changed_by": self.changed_by,
            "created_at": self.created_at,
        }

    @classmethod
    def create_change(cls, content_id: str, old: Dict[str, Any],
                       new: Dict[str, Any], reason: str,
                       score: float = 0.0) -> "MappingHistory":
        return cls(
            content_id=content_id,
            old_mapping=old,
            new_mapping=new,
            reason=reason,
            ai_score=score,
        )
