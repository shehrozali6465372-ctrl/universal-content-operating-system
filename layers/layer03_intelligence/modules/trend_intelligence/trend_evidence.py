"""Trend Evidence - Evidence-based reasoning for trend analysis."""
from __future__ import annotations
from typing import Dict, List, Optional


class EvidenceItem:
    """A single piece of evidence supporting a trend conclusion."""
    __slots__ = ("source", "claim", "strength", "data_point", "category")

    def __init__(self, source: str = "", claim: str = "", strength: float = 0.0,
                 data_point: Optional[str] = None, category: str = "observation"):
        self.source = source
        self.claim = claim
        self.strength = strength
        self.data_point = data_point
        self.category = category  # observation, measurement, prediction, comparison

    def to_dict(self) -> Dict:
        return {
            "source": self.source, "claim": self.claim,
            "strength": round(self.strength, 3),
            "data_point": self.data_point, "category": self.category,
        }


class TrendEvidence:
    """Collects and organizes evidence for a trend analysis."""
    __slots__ = ("topic", "evidence_items", "reasoning_steps", "conclusion",
                 "overall_strength", "counter_evidence")

    def __init__(self, topic: str = "") -> None:
        self.topic = topic
        self.evidence_items: List[EvidenceItem] = []
        self.reasoning_steps: List[str] = []
        self.conclusion = ""
        self.overall_strength = 0.0
        self.counter_evidence: List[EvidenceItem] = []

    def add_evidence(self, source: str, claim: str, strength: float = 0.5,
                     data_point: Optional[str] = None, category: str = "observation") -> None:
        self.evidence_items.append(EvidenceItem(source, claim, strength, data_point, category))

    def add_counter_evidence(self, source: str, claim: str, strength: float = 0.5) -> None:
        self.counter_evidence.append(EvidenceItem(source, claim, strength, category="counter"))

    def add_reasoning(self, step: str) -> None:
        self.reasoning_steps.append(step)

    def calculate_strength(self) -> float:
        if not self.evidence_items:
            return 0.0
        pos = sum(e.strength for e in self.evidence_items)
        neg = sum(e.strength for e in self.counter_evidence)
        total = pos + neg
        self.overall_strength = max(0.0, min(1.0, (pos - neg * 0.5) / max(total, 1.0)))
        return self.overall_strength

    def to_dict(self) -> Dict:
        return {
            "topic": self.topic,
            "evidence": [e.to_dict() for e in self.evidence_items],
            "counter_evidence": [e.to_dict() for e in self.counter_evidence],
            "reasoning": list(self.reasoning_steps),
            "conclusion": self.conclusion,
            "overall_strength": round(self.overall_strength, 3),
        }


class TrendEvidenceBuilder:
    """Builds evidence from trend analysis results."""

    def build(self, topic: str, analysis: Dict) -> TrendEvidence:
        evidence = TrendEvidence(topic)

        # Momentum evidence
        momentum = analysis.get("momentum", {})
        velocity = momentum.get("velocity", 0)
        if velocity > 0.3:
            evidence.add_evidence(
                "MomentumAnalyzer", f"Velocity is positive at {velocity:.2f}",
                min(1.0, velocity), f"velocity={velocity:.2f}", "measurement"
            )
            evidence.add_reasoning(f"Momentum increasing (velocity: {velocity:.2f})")
        elif velocity < -0.3:
            evidence.add_counter_evidence(
                "MomentumAnalyzer", f"Velocity is negative at {velocity:.2f}",
                min(1.0, abs(velocity))
            )
            evidence.add_reasoning(f"Momentum decreasing (velocity: {velocity:.2f})")

        # Lifecycle evidence
        lifecycle = analysis.get("lifecycle", {})
        stage = lifecycle.get("stage", "unknown")
        if stage in ("emerging", "growing"):
            evidence.add_evidence(
                "LifecycleDetector", f"Trend is in {stage} stage",
                0.8 if stage == "growing" else 0.6, f"stage={stage}", "observation"
            )
            evidence.add_reasoning(f"Lifecycle stage: {stage} - opportunity available")
        elif stage in ("declining", "dead"):
            evidence.add_counter_evidence(
                "LifecycleDetector", f"Trend is in {stage} stage",
                0.8 if stage == "dead" else 0.6
            )

        # Cross-platform evidence
        platforms = analysis.get("cross_platform", {})
        pc = platforms.get("platform_count", 0)
        consensus = platforms.get("consensus_level", 0)
        if pc >= 3:
            evidence.add_evidence(
                "CrossPlatformFusion", f"Trending on {pc} platforms with {consensus:.0%} consensus",
                min(1.0, pc / 3.0 * consensus), f"platforms={pc}", "measurement"
            )
            evidence.add_reasoning(f"Cross-platform presence: {pc} platforms, consensus: {consensus:.0%}")

        # Virality evidence
        virality = analysis.get("virality", {})
        vp = virality.get("viral_probability", 0)
        if vp > 0.5:
            evidence.add_evidence(
                "ViralityPredictor", f"Viral probability at {vp:.0%}",
                vp, f"probability={vp:.2f}", "prediction"
            )

        # Confidence evidence
        confidence = analysis.get("confidence", {})
        oc = confidence.get("overall_confidence", 0)
        if oc > 0.7:
            evidence.add_evidence(
                "TrendConfidence", f"Overall confidence is {oc:.0%}",
                oc, f"confidence={oc:.2f}", "measurement"
            )

        # Seasonality evidence
        seasonality = analysis.get("seasonality", {})
        strength = seasonality.get("strength", 0)
        if strength > 0.5:
            evidence.add_evidence(
                "SeasonalityAnalyzer", f"Seasonal pattern detected (strength: {strength:.2f})",
                strength, f"period={seasonality.get('period_days', 0)}d", "observation"
            )
            evidence.add_reasoning(f"Seasonal pattern: {seasonality.get('pattern_type', 'unknown')}")

        # Competition evidence
        competition = analysis.get("competition", {})
        level = competition.get("level", "unknown")
        if level == "low":
            evidence.add_evidence(
                "Competition", "Low competition detected",
                0.7, "level=low", "observation"
            )
        elif level == "high":
            evidence.add_counter_evidence("Competition", "High competition detected", 0.7)

        # Calculate overall
        evidence.calculate_strength()
        return evidence
