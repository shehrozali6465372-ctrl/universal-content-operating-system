"""Explanation Builder - Generates explainable reasons for recommendations."""
from __future__ import annotations
from typing import Any, Dict, List


class Explanation:
    __slots__ = ("topic", "why", "why_not", "alternatives", "confidence_explanation")
    def __init__(self, topic: str = "") -> None:
        self.topic = topic
        self.why: List[str] = []
        self.why_not: List[str] = []
        self.alternatives: List[str] = []
        self.confidence_explanation = ""
    def to_dict(self) -> Dict:
        return {"topic": self.topic, "why": list(self.why), "why_not": list(self.why_not),
                "alternatives": list(self.alternatives), "confidence_explanation": self.confidence_explanation}


class ExplanationBuilder:
    def build(self, candidate: Any, rank_info: Dict = None) -> Explanation:
        exp = Explanation(candidate.topic)
        signals = getattr(candidate, "signals", getattr(candidate, "signal_scores", {}))
        score = getattr(candidate, "final_score", getattr(candidate, "base_score", 0))

        if signals.get("trend_score", 0) > 0.7:
            exp.why.append("High trend score")
        if signals.get("audience_demand", 0) > 0.7:
            exp.why.append("Strong audience demand")
        if signals.get("competitor_gap", 0) > 0.6:
            exp.why.append("Competitor gap identified")
        if signals.get("knowledge_relevance", 0) > 0.7:
            exp.why.append("High knowledge relevance")
        if signals.get("freshness", 0) > 0.8:
            exp.why.append("Fresh and timely content")

        if signals.get("trend_score", 1) < 0.3:
            exp.why_not.append("Low trend score")
        if signals.get("competitor_gap", 1) < 0.2:
            exp.why_not.append("High competition")
        if signals.get("freshness", 1) < 0.3:
            exp.why_not.append("Content may be outdated")

        if score >= 0.8:
            exp.confidence_explanation = f"High confidence ({score:.0%}): strong signals across dimensions"
        elif score >= 0.5:
            exp.confidence_explanation = f"Moderate confidence ({score:.0%}): some uncertainty"
        else:
            exp.confidence_explanation = f"Low confidence ({score:.0%}): limited signals"

        return exp
