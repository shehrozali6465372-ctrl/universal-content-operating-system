"""Fusion Engine — combines Layer 2 outputs into unified intelligence."""
from typing import Dict, List

class FusedIntelligence:
    __slots__ = ("topic", "sources", "confidence", "evidence", "insights", "conflicts_resolved")
    def __init__(self, topic: str = ""):
        self.topic = topic
        self.sources: List[str] = []
        self.confidence = 0.0
        self.evidence: List[str] = []
        self.insights: List[str] = []
        self.conflicts_resolved: List[Dict] = []
    def to_dict(self) -> dict:
        return {"topic": self.topic, "sources": self.sources, "confidence": self.confidence,
                "evidence": self.evidence, "insights": self.insights, "conflicts_resolved": self.conflicts_resolved}

class FusionEngine:
    def __init__(self, min_sources: int = 2):
        self.min_sources = min_sources
    def fuse(self, data: List[Dict], topic: str = "") -> FusedIntelligence:
        result = FusedIntelligence(topic)
        if not data: return result
        all_confidences = []
        all_evidence = []
        all_insights = []
        seen_sources = set()
        for d in data:
            source = d.get("source", "unknown")
            seen_sources.add(source)
            result.sources.append(source)
            conf = d.get("confidence", 0.5)
            all_confidences.append(conf)
            all_evidence.extend(d.get("evidence", []))
            all_insights.extend(d.get("insights", []))
        result.sources = list(seen_sources)
        result.confidence = round(sum(all_confidences) / max(len(all_confidences), 1), 3)
        result.evidence = list(dict.fromkeys(all_evidence))
        result.insights = list(dict.fromkeys(all_insights))
        if len(result.sources) >= self.min_sources:
            result.confidence = min(1.0, result.confidence * 1.1)
        return result
    def resolve_conflict(self, values: List[Dict]) -> Dict:
        if not values: return {}
        if len(values) == 1: return values[0]
        avg_score = sum(v.get("score", 0) for v in values) / len(values)
        best = max(values, key=lambda v: v.get("confidence", 0))
        return {"resolved_value": best.get("score", avg_score), "method": "highest_confidence", "original_count": len(values)}
