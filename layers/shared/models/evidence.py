"""
Shared Evidence Models
Frozen interface — v1.0.0
"""

from datetime import datetime, timezone
from typing import List


class Evidence:
    """A single piece of evidence supporting a claim or decision."""

    __slots__ = (
        "evidence_id", "claim", "source", "source_url",
        "credibility", "freshness", "content",
        "verified", "created_at",
    )

    def __init__(
        self,
        claim: str,
        source: str = "",
        source_url: str = "",
        credibility: float = 0.5,
        freshness: float = 0.5,
        content: str = "",
        verified: bool = False,
    ):
        self.evidence_id = f"ev_{hash(claim) % 1000000}"
        self.claim = claim
        self.source = source
        self.source_url = source_url
        self.credibility = max(0.0, min(1.0, credibility))
        self.freshness = max(0.0, min(1.0, freshness))
        self.content = content
        self.verified = verified
        self.created_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "evidence_id": self.evidence_id,
            "claim": self.claim,
            "source": self.source,
            "source_url": self.source_url,
            "credibility": self.credibility,
            "freshness": self.freshness,
            "content": self.content,
            "verified": self.verified,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Evidence":
        e = cls(
            claim=data.get("claim", ""),
            source=data.get("source", ""),
            source_url=data.get("source_url", ""),
            credibility=data.get("credibility", 0.5),
            freshness=data.get("freshness", 0.5),
            content=data.get("content", ""),
            verified=data.get("verified", False),
        )
        e.evidence_id = data.get("evidence_id", e.evidence_id)
        e.created_at = data.get("created_at", e.created_at)
        return e

    def quality_score(self) -> float:
        """Combined quality score of this evidence."""
        return round((self.credibility * 0.6 + self.freshness * 0.4), 3)

    def __repr__(self) -> str:
        return f"Evidence(claim='{self.claim[:50]}', credibility={self.credibility})"


class EvidenceBundle:
    """Collection of evidence pieces for a topic or decision."""

    __slots__ = ("topic", "evidence_list", "overall_credibility", "created_at")

    def __init__(self, topic: str = ""):
        self.topic = topic
        self.evidence_list: List[Evidence] = []
        self.overall_credibility = 0.0
        self.created_at = datetime.now(timezone.utc).isoformat()

    def add(self, evidence: Evidence):
        self.evidence_list.append(evidence)
        self._recalculate()

    def remove(self, evidence_id: str) -> bool:
        for i, e in enumerate(self.evidence_list):
            if e.evidence_id == evidence_id:
                self.evidence_list.pop(i)
                self._recalculate()
                return True
        return False

    def get_verified(self) -> List[Evidence]:
        return [e for e in self.evidence_list if e.verified]

    def get_unverified(self) -> List[Evidence]:
        return [e for e in self.evidence_list if not e.verified]

    def count(self) -> int:
        return len(self.evidence_list)

    def _recalculate(self):
        if not self.evidence_list:
            self.overall_credibility = 0.0
            return
        self.overall_credibility = round(
            sum(e.credibility for e in self.evidence_list) / len(self.evidence_list), 3
        )

    def to_dict(self) -> dict:
        return {
            "topic": self.topic,
            "evidence_list": [e.to_dict() for e in self.evidence_list],
            "overall_credibility": self.overall_credibility,
            "count": self.count(),
            "created_at": self.created_at,
        }

    def __repr__(self) -> str:
        return f"EvidenceBundle(topic='{self.topic}', count={self.count()})"
