"""Draft Memory — Store and retrieve past drafts."""
from __future__ import annotations
import time
from threading import RLock
from uuid import uuid4
from typing import Any, Dict, List


class DraftRecord:
    """A stored draft record."""
    __slots__ = ("record_id", "plan_id", "topic", "text", "variant_type",
                 "provider", "model", "tokens_used", "metadata", "created_at")

    def __init__(self, plan_id: str = "", topic: str = "", text: str = "") -> None:
        self.record_id = f"drec_{uuid4().hex}"
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
        if max_size < 1:
            raise ValueError("max_size must be >= 1")
        self._records: List[DraftRecord] = []
        self._max_size = max_size
        self._topic_index: Dict[str, List[int]] = {}
        self._lock = RLock()

    def store(self, plan_id: str, topic: str, text: str, variant_type: str = "original",
              provider: str = "", model: str = "", tokens: int = 0) -> DraftRecord:
        """Store a new draft."""
        rec = DraftRecord(plan_id=plan_id, topic=topic, text=text)
        rec.variant_type = variant_type
        rec.provider = provider
        rec.model = model
        rec.tokens_used = tokens

        with self._lock:
            if len(self._records) >= self._max_size:
                self._records.pop(0)
            self._rebuild_index_locked()
            self._records.append(rec)
            self._rebuild_index_locked()
        return rec

    def get_by_topic(self, topic: str, limit: int = 5) -> List[DraftRecord]:
        if limit < 1:
            return []
        with self._lock:
            idxs = self._topic_index.get(topic.lower(), [])
            return [self._copy_record(self._records[i]) for i in idxs if i < len(self._records)][:limit]

    def get_by_plan(self, plan_id: str) -> List[DraftRecord]:
        with self._lock:
            return [self._copy_record(r) for r in self._records if r.plan_id == plan_id]

    def get_recent(self, limit: int = 10) -> List[DraftRecord]:
        if limit < 1:
            return []
        with self._lock:
            return [self._copy_record(r) for r in self._records[-limit:]]

    @staticmethod
    def _copy_record(record: DraftRecord) -> DraftRecord:
        copy = DraftRecord(record.plan_id, record.topic, record.text)
        copy.record_id = record.record_id
        copy.variant_type = record.variant_type
        copy.provider = record.provider
        copy.model = record.model
        copy.tokens_used = record.tokens_used
        copy.metadata = dict(record.metadata)
        copy.created_at = record.created_at
        return copy

    def _rebuild_index_locked(self) -> None:
        self._topic_index = {}
        for idx, record in enumerate(self._records):
            self._topic_index.setdefault(record.topic.lower(), []).append(idx)

    @property
    def count(self) -> int:
        with self._lock:
            return len(self._records)

    @property
    def total_tokens(self) -> int:
        with self._lock:
            return sum(r.tokens_used for r in self._records)
