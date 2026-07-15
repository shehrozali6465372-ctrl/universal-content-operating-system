"""Draft Memory — Store and retrieve past drafts."""
from __future__ import annotations
import time
from typing import Any, Dict, List


class DraftRecord:
    """A stored draft record."""
    __slots__ = ("record_id", "plan_id", "topic", "text", "variant_type",
                 "provider", "model", "tokens_used", "metadata", "created_at")

    def __init__(self, plan_id: str = "", topic: str = "", text: str = "") -> None:
        self.record_id = f"drec_{int(time.time() * 1000) % 10000000}"
        self.plan_id = plan_id
        self.topic = topic
        self.text = text
        self.variant_type = "original"
        self.provider = ""
        self.model = ""
        self.tokens_used = 0
        self.metadata: Dict[str, Any] = {}
        self.created_at = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "record_id": self.record_id,
            "plan_id": self.plan_id,
            "topic": self.topic,
            "text_preview": self.text[:100] + "..." if len(self.text) > 100 else self.text,
            "variant_type": self.variant_type,
            "provider": self.provider,
            "tokens_used": self.tokens_used,
        }


class DraftMemory:
    """Stores and retrieves past drafts."""

    def __init__(self, max_size: int = 200) -> None:
        self._records: List[DraftRecord] = []
        self._max_size = max_size
        self._topic_index: Dict[str, List[int]] = {}

    def store(self, plan_id: str, topic: str, text: str, variant_type: str = "original",
              provider: str = "", model: str = "", tokens: int = 0) -> DraftRecord:
        """Store a new draft."""
        rec = DraftRecord(plan_id=plan_id, topic=topic, text=text)
        rec.variant_type = variant_type
        rec.provider = provider
        rec.model = model
        rec.tokens_used = tokens

        if len(self._records) >= self._max_size:
            self._records.pop(0)

        idx = len(self._records)
        self._records.append(rec)
        self._topic_index.setdefault(topic.lower(), []).append(idx)
        return rec

    def get_by_topic(self, topic: str, limit: int = 5) -> List[DraftRecord]:
        idxs = self._topic_index.get(topic.lower(), [])
        return [self._records[i] for i in idxs if i < len(self._records)][:limit]

    def get_by_plan(self, plan_id: str) -> List[DraftRecord]:
        return [r for r in self._records if r.plan_id == plan_id]

    def get_recent(self, limit: int = 10) -> List[DraftRecord]:
        return self._records[-limit:]

    @property
    def count(self) -> int:
        return len(self._records)

    @property
    def total_tokens(self) -> int:
        return sum(r.tokens_used for r in self._records)
