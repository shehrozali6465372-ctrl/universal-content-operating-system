"""MappingHistory — Track changes and AI decisions for content mappings."""
from __future__ import annotations
import time
import uuid
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class MappingHistory:
    """Record of mapping changes, AI decisions, and overrides."""

    history_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    mapping_id: str = ""
    article_id: str = ""

    old_mapping: Dict[str, Any] = field(default_factory=dict)
    new_mapping: Dict[str, Any] = field(default_factory=dict)

    change_type: str = ""  # auto, manual_override, ai_update, validation
    change_reason: str = ""
    ai_score: float = 0.0
    decided_by: str = "ai"

    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "history_id": self.history_id,
            "mapping_id": self.mapping_id,
            "change_type": self.change_type,
            "change_reason": self.change_reason[:100],
            "ai_score": round(self.ai_score, 2),
            "decided_by": self.decided_by,
            "created_at": self.created_at,
        }
