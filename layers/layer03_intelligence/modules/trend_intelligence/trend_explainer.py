"""Trend Explainer - Provides human-readable explanations for trend signals."""
from __future__ import annotations
from typing import Dict, List


class TrendExplanation:
    """Human-readable explanation for why a trend is significant."""
    __slots__ = ("topic", "summary", "factors", "confidence", "recommendation",
                 "risk_warnings", "evidence")

    def __init__(self, topic: str = "") -> None:
        self.topic = topic
        self.summary = ""
        self.factors: List[str] = []
        self.confidence = 0.0
        self.recommendation = ""
        self.risk_warnings: List[str] = []
        self.evidence: List[str] = []

    def to_dict(self) -> Dict:
        return {
            "topic": self.topic, "summary": self.summary,
            "factors": list(self.factors), "confidence": round(self.confidence, 3),
            "recommendation": self.recommendation,
            "risk_warnings": list(self.risk_warnings),
            "evidence": list(self.evidence),
        }


class TrendExplainer:
    """Generates explanations for trend analysis results."""

    def explain(self, topic: str, analysis: Dict) -> TrendExplanation:
        result = TrendExplanation(topic)
        factors = []
        risks = []
        evidence = []

        momentum = analysis.get("momentum", {})
        velocity = momentum.get("velocity", 0)
        if velocity > 0.5:
            factors.append("Strong upward momentum")
            evidence.append("Momentum accelerating")
        elif velocity < -0.3:
            risks.append("Declining momentum detected")

        lifecycle = analysis.get("lifecycle", {})
        stage = lifecycle.get("stage", "unknown")
        if stage == "emerging":
            factors.append("Trend is in emerging stage - high opportunity")
        elif stage == "peak":
            risks.append("Trend may be at its peak")
        elif stage == "declining":
            risks.append("Trend is declining")

        platforms = analysis.get("platforms", {})
        pc = platforms.get("platform_count", 0)
        if pc >= 3:
            factors.append(f"Trending on {pc} platforms")

        virality = analysis.get("virality", {})
        vp = virality.get("viral_probability", 0)
        if vp > 0.7:
            factors.append("High viral potential")
        elif vp > 0.4:
            factors.append("Moderate viral potential")

        competition = analysis.get("competition", {})
        if competition.get("level") == "low":
            factors.append("Low competition")
        elif competition.get("level") == "high":
            risks.append("High competition")

        result.factors = factors
        result.risk_warnings = risks
        result.evidence = evidence
        result.confidence = analysis.get("confidence", {}).get("overall_confidence", 0.5)

        if factors:
            result.summary = f"'{topic}' is trending because: " + "; ".join(factors[:3]) + "."
        else:
            result.summary = f"'{topic}' has limited trend signals."

        if result.risk_warnings:
            result.recommendation = f"Proceed with caution for '{topic}'"
        elif factors:
            result.recommendation = f"Good opportunity to create content about '{topic}'"
        else:
            result.recommendation = f"Insufficient data for '{topic}'"

        return result
