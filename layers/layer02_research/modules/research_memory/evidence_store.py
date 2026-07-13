"""
Evidence Store
Layer 2: Research Engine — Module 7

Stores and retrieves evidence for research decisions:
- Evidence CRUD
- Evidence ranking by credibility
- Evidence aggregation by topic
- Cross-reference support
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional


class EvidenceItem:
    """A single evidence item."""

    __slots__ = (
        "evidence_id", "claim_id", "text", "source",
        "credibility", "supports", "topic",
        "created_at", "metadata",
    )

    def __init__(self, evidence_id: str, claim_id: str = "", text: str = "",
                 source: str = "", credibility: float = 0.5, supports: bool = True,
                 topic: str = "general"):
        self.evidence_id = evidence_id
        self.claim_id = claim_id
        self.text = text
        self.source = source
        self.credibility = max(0.0, min(1.0, credibility))
        self.supports = supports
        self.topic = topic
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.metadata: Dict = {}

    def to_dict(self) -> dict:
        return {
            "evidence_id": self.evidence_id, "claim_id": self.claim_id,
            "text": self.text[:300], "source": self.source,
            "credibility": self.credibility, "supports": self.supports,
            "topic": self.topic, "created_at": self.created_at,
        }


class EvidenceStore:
    """Storage and retrieval for evidence items."""

    def __init__(self):
        self._items: Dict[str, EvidenceItem] = {}
        self._topic_index: Dict[str, List[str]] = {}
        self._claim_index: Dict[str, List[str]] = {}

    def add(self, item: EvidenceItem) -> str:
        self._items[item.evidence_id] = item
        self._topic_index.setdefault(item.topic, []).append(item.evidence_id)
        self._claim_index.setdefault(item.claim_id, []).append(item.evidence_id)
        return item.evidence_id

    def get(self, evidence_id: str) -> Optional[EvidenceItem]:
        return self._items.get(evidence_id)

    def remove(self, evidence_id: str) -> bool:
        if evidence_id in self._items:
            item = self._items.pop(evidence_id)
            if item.topic in self._topic_index:
                self._topic_index[item.topic] = [
                    eid for eid in self._topic_index[item.topic] if eid != evidence_id
                ]
            return True
        return False

    def get_by_topic(self, topic: str) -> List[EvidenceItem]:
        eids = self._topic_index.get(topic, [])
        return [self._items[eid] for eid in eids if eid in self._items]

    def get_by_claim(self, claim_id: str) -> List[EvidenceItem]:
        eids = self._claim_index.get(claim_id, [])
        return [self._items[eid] for eid in eids if eid in self._items]

    def get_supporting(self, topic: str) -> List[EvidenceItem]:
        return [e for e in self.get_by_topic(topic) if e.supports]

    def get_contradicting(self, topic: str) -> List[EvidenceItem]:
        return [e for e in self.get_by_topic(topic) if not e.supports]

    def get_top_credible(self, count: int = 10) -> List[EvidenceItem]:
        return sorted(self._items.values(), key=lambda e: e.credibility, reverse=True)[:count]

    def aggregate_confidence(self, topic: str) -> float:
        """Aggregate confidence from all evidence on a topic."""
        items = self.get_by_topic(topic)
        if not items:
            return 0.0
        supporting = [e for e in items if e.supports]
        total = len(items)
        support_ratio = len(supporting) / total if total > 0 else 0
        avg_credibility = sum(e.credibility for e in items) / total
        return round(support_ratio * avg_credibility, 3)

    def size(self) -> int:
        return len(self._items)

    def stats(self) -> dict:
        topics = set(e.topic for e in self._items.values())
        supporting = sum(1 for e in self._items.values() if e.supports)
        return {
            "total_evidence": len(self._items),
            "topics": len(topics),
            "supporting": supporting,
            "contradicting": len(self._items) - supporting,
        }
