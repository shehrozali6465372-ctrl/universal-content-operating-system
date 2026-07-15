"""Evidence Aggregator - Aggregates evidence from multiple intelligence sources."""
from __future__ import annotations
from typing import Dict, List


class AggregatedEvidence:
    __slots__ = ("topic", "supporting", "contradicting", "net_strength", "source_count")
    def __init__(self, topic: str = "") -> None:
        self.topic = topic
        self.supporting: List[Dict] = []
        self.contradicting: List[Dict] = []
        self.net_strength = 0.0
        self.source_count = 0
    def to_dict(self) -> Dict:
        return {"topic": self.topic, "supporting_count": len(self.supporting),
                "contradicting_count": len(self.contradicting),
                "net_strength": round(self.net_strength, 3), "source_count": self.source_count}


class EvidenceAggregator:
    def aggregate(self, topic: str, evidence_lists: List[Dict]) -> AggregatedEvidence:
        result = AggregatedEvidence(topic)
        for ev in evidence_lists:
            items = ev.get("evidence", [])
            source = ev.get("source", "unknown")
            for item in items:
                entry = {"text": str(item), "source": source}
                strength = ev.get("strength", 0.5)
                if strength >= 0.5:
                    result.supporting.append(entry)
                else:
                    result.contradicting.append(entry)
            result.source_count += 1

        pos = len(result.supporting)
        neg = len(result.contradicting)
        total = pos + neg
        result.net_strength = (pos - neg) / max(total, 1) if total > 0 else 0.0
        return result
