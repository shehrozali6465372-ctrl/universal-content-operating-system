"""Explanation Generator - Generates human-readable explanations for decisions."""
from __future__ import annotations
from typing import Dict, List


class Explanation:
    """A structured explanation for a decision or analysis."""
    __slots__ = ("title", "summary", "sections", "evidence", "confidence",
                 "recommendation", "caveats")

    def __init__(self, title: str = "") -> None:
        self.title = title
        self.summary = ""
        self.sections: List[Dict[str, str]] = []
        self.evidence: List[str] = []
        self.confidence = 0.0
        self.recommendation = ""
        self.caveats: List[str] = []

    def add_section(self, heading: str, content: str) -> None:
        self.sections.append({"heading": heading, "content": content})

    def to_dict(self) -> Dict:
        return {
            "title": self.title, "summary": self.summary,
            "sections": list(self.sections), "evidence": list(self.evidence),
            "confidence": round(self.confidence, 3),
            "recommendation": self.recommendation, "caveats": list(self.caveats),
        }

    def to_text(self) -> str:
        lines = [f"# {self.title}", "", self.summary, ""]
        for s in self.sections:
            lines.append(f"## {s['heading']}")
            lines.append(s["content"])
            lines.append("")
        if self.evidence:
            lines.append("## Evidence")
            for e in self.evidence:
                lines.append(f"- {e}")
            lines.append("")
        if self.recommendation:
            lines.append("## Recommendation")
            lines.append(self.recommendation)
        return "\n".join(lines)


class ExplanationGenerator:
    """Generates explanations from analysis data."""

    def generate(self, title: str, analysis: Dict) -> Explanation:
        exp = Explanation(title)
        sections = []

        # Momentum section
        momentum = analysis.get("momentum", {})
        if momentum:
            direction = momentum.get("direction", "unknown")
            velocity = momentum.get("velocity", 0)
            sections.append({
                "heading": "Momentum",
                "content": f"Trend momentum is {direction} with velocity {velocity:.2f}. "
                          f"{'This indicates growing interest.' if velocity > 0 else 'This indicates declining interest.'}",
            })

        # Lifecycle section
        lifecycle = analysis.get("lifecycle", {})
        if lifecycle:
            stage = lifecycle.get("stage", "unknown")
            confidence = lifecycle.get("confidence", 0)
            sections.append({
                "heading": "Lifecycle Stage",
                "content": f"The trend is currently in the {stage} stage "
                          f"(confidence: {confidence:.0%}).",
            })

        # Confidence section
        confidence = analysis.get("confidence", {})
        if confidence:
            overall = confidence.get("overall_confidence", 0)
            breakdown = confidence.get("breakdown", {})
            parts = [f"{k}: {v:.0%}" for k, v in breakdown.items() if k.startswith("weighted_")]
            sections.append({
                "heading": "Confidence Analysis",
                "content": f"Overall confidence: {overall:.0%}. Breakdown: {', '.join(parts)}.",
            })

        # Virality section
        virality = analysis.get("virality", {})
        if virality:
            prob = virality.get("viral_probability", 0)
            sections.append({
                "heading": "Virality Assessment",
                "content": f"Viral probability: {prob:.0%}.",
            })

        # Build summary
        if sections:
            exp.summary = f"Analysis of '{title}' based on {len(sections)} dimensions."
        else:
            exp.summary = f"Insufficient data for comprehensive analysis of '{title}'."

        exp.sections = sections
        exp.confidence = confidence.get("overall_confidence", 0) if confidence else 0.0

        # Recommendation
        if exp.confidence > 0.7:
            exp.recommendation = f"Good opportunity to create content about '{title}'"
        elif exp.confidence > 0.4:
            exp.recommendation = f"Moderate opportunity for '{title}' - proceed with caution"
        else:
            exp.recommendation = f"Insufficient confidence for '{title}' - gather more data"

        return exp

    def generate_from_decision(self, title: str, chosen: str, alternatives: List[str],
                               reasoning: List[str], confidence: float) -> Explanation:
        exp = Explanation(title)
        exp.summary = f"Decision: '{chosen}' selected for {title}."
        exp.confidence = confidence
        exp.add_section("Decision", f"Selected option: '{chosen}'")
        if alternatives:
            exp.add_section("Alternatives Considered", ", ".join(alternatives))
        if reasoning:
            exp.add_section("Reasoning", " ".join(reasoning))
        if confidence > 0.7:
            exp.recommendation = f"High confidence decision - proceed with '{chosen}'"
        else:
            exp.recommendation = f"Moderate confidence - monitor results for '{chosen}'"
        return exp
