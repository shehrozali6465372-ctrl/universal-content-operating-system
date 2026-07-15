"""Candidate Generator - Generates candidate recommendations from multiple sources."""
from __future__ import annotations
from typing import Dict, List


class Candidate:
    """A candidate recommendation before ranking."""
    __slots__ = ("topic", "source", "base_score", "metadata", "signals")

    def __init__(self, topic: str = "", source: str = "", base_score: float = 0.0):
        self.topic = topic
        self.source = source
        self.base_score = base_score
        self.metadata: Dict = {}
        self.signals: Dict[str, float] = {}

    def to_dict(self) -> Dict:
        return {"topic": self.topic, "source": self.source, "base_score": round(self.base_score, 3),
                "signals": {k: round(v, 3) for k, v in self.signals.items()}}


class CandidateGenerator:
    """Generates candidates from trend, audience, competitor, and knowledge data."""

    def __init__(self) -> None:
        self._sources: List[str] = []

    def generate_from_trends(self, trends: List[Dict]) -> List[Candidate]:
        candidates = []
        for t in trends:
            c = Candidate(t.get("topic", ""), "trend", t.get("score", 0.5))
            c.signals["trend_score"] = t.get("score", 0.5)
            c.signals["momentum"] = t.get("momentum", 0.5)
            candidates.append(c)
        return candidates

    def generate_from_audience(self, gaps: List[Dict]) -> List[Candidate]:
        candidates = []
        for g in gaps:
            c = Candidate(g.get("topic", ""), "audience_gap", g.get("demand", 0.5))
            c.signals["audience_demand"] = g.get("demand", 0.5)
            c.signals["competition"] = g.get("competition", 0.5)
            candidates.append(c)
        return candidates

    def generate_from_competitor(self, opportunities: List[Dict]) -> List[Candidate]:
        candidates = []
        for o in opportunities:
            c = Candidate(o.get("topic", ""), "competitor_gap", o.get("opportunity", 0.5))
            c.signals["competitor_gap"] = o.get("gap_score", 0.5)
            candidates.append(c)
        return candidates

    def generate_from_knowledge(self, knowledge: List[Dict]) -> List[Candidate]:
        candidates = []
        for k in knowledge:
            c = Candidate(k.get("topic", ""), "knowledge", k.get("relevance", 0.5))
            c.signals["knowledge_relevance"] = k.get("relevance", 0.5)
            c.signals["freshness"] = k.get("freshness", 0.5)
            candidates.append(c)
        return candidates

    def merge_candidates(self, all_candidates: List[List[Candidate]]) -> List[Candidate]:
        merged: Dict[str, Candidate] = {}
        for group in all_candidates:
            for c in group:
                key = c.topic.lower()
                if key in merged:
                    existing = merged[key]
                    existing.base_score = max(existing.base_score, c.base_score)
                    existing.signals.update(c.signals)
                else:
                    merged[key] = c
        return list(merged.values())
