"""Strategy Explainer — Generate human-readable strategy explanations."""
from __future__ import annotations
from typing import Any, Dict, List, Optional


class StrategyExplanation:
    """Human-readable explanation of a strategy."""
    __slots__ = ("strategy_id", "summary", "why_this", "alternatives",
                 "risks", "expected_results", "confidence_explanation",
                 "full_text", "sections")

    def __init__(self, strategy_id: str = "") -> None:
        self.strategy_id = strategy_id
        self.summary = ""
        self.why_this: List[str] = []
        self.alternatives: List[str] = []
        self.risks: List[str] = []
        self.expected_results: List[str] = []
        self.confidence_explanation = ""
        self.full_text = ""
        self.sections: Dict[str, str] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "strategy_id": self.strategy_id,
            "summary": self.summary,
            "why_this": self.why_this,
            "alternatives": self.alternatives,
            "risks": self.risks,
            "expected_results": self.expected_results,
            "confidence_explanation": self.confidence_explanation,
            "sections": self.sections,
        }


class StrategyExplainer:
    """Generates explanations for strategies."""

    def explain(self, strategy_data: Dict[str, Any], eval_data: Optional[Dict] = None,
                risk_data: Optional[Dict] = None) -> StrategyExplanation:
        """Generate a full explanation for a strategy."""
        sid = strategy_data.get("strategy_id", strategy_data.get("name", ""))
        result = StrategyExplanation(strategy_id=sid)

        # Summary
        result.summary = self._build_summary(strategy_data)

        # Why this strategy
        result.why_this = self._build_why(strategy_data, eval_data)

        # Alternatives considered
        result.alternatives = self._build_alternatives(strategy_data)

        # Risks
        result.risks = self._build_risks(risk_data)

        # Expected results
        result.expected_results = self._build_expected(strategy_data, eval_data)

        # Confidence
        result.confidence_explanation = self._explain_confidence(strategy_data, eval_data)

        # Full text
        result.full_text = self._assemble_full_text(result)

        # Sections
        result.sections = {
            "summary": result.summary,
            "reasoning": " | ".join(result.why_this),
            "risks": " | ".join(result.risks) if result.risks else "Minimal risk identified",
            "expected": " | ".join(result.expected_results),
        }

        return result

    def explain_selection(self, selection_data: Dict[str, Any]) -> str:
        """Explain why a strategy was selected over alternatives."""
        selected = selection_data.get("selected", "")
        ranking = selection_data.get("ranking", [])
        reasoning = selection_data.get("reasoning", [])

        parts = [f"Strategy '{selected}' was selected"]
        if ranking:
            parts.append(f"out of {len(ranking)} alternatives")
        parts.extend(reasoning)
        return ". ".join(parts) + "."

    def explain_risk(self, risk_data: Dict[str, Any]) -> str:
        """Explain risk assessment in plain language."""
        level = risk_data.get("risk_level", "medium")
        score = risk_data.get("overall_risk", 0.5)
        mitigations = risk_data.get("mitigations", [])
        parts = [f"Overall risk level: {level} (score: {score:.2f})"]
        if mitigations:
            parts.append(f"Recommended mitigations: {len(mitigations)}")
        return ". ".join(parts)

    def _build_summary(self, data: Dict[str, Any]) -> str:
        name = data.get("name", "Unnamed strategy")
        horizon = data.get("horizon", "short")
        confidence = data.get("confidence", 0)
        return f"{name} ({horizon}-term) with {confidence:.0%} confidence"

    def _build_why(self, data: Dict, eval_data: Optional[Dict]) -> List[str]:
        reasons: List[str] = []
        reasoning = data.get("reasoning", [])
        if reasoning:
            reasons.extend(reasoning)
        if eval_data:
            strengths = eval_data.get("strengths", [])
            reasons.extend(strengths)
        if not reasons:
            reasons.append("Based on combined intelligence scoring")
        return reasons

    def _build_alternatives(self, data: Dict) -> List[str]:
        alts: List[str] = []
        risk = data.get("risk_level", "medium")
        if risk == "high":
            alts.append("Lower-risk variant with reduced scope")
        if data.get("horizon") == "short":
            alts.append("Long-term authority-building approach")
        if not alts:
            alts.append("Alternative strategies evaluated and filtered out")
        return alts

    def _build_risks(self, risk_data: Optional[Dict]) -> List[str]:
        if not risk_data:
            return []
        risks: List[str] = []
        for factor in risk_data.get("risk_factors", []):
            if factor.get("level") == "high":
                risks.append(f"High risk: {factor.get('factor', 'unknown')}")
        if not risks:
            risks.append("No significant risks identified")
        return risks

    def _build_expected(self, data: Dict, eval_data: Optional[Dict]) -> List[str]:
        expected: List[str] = []
        if eval_data:
            outcomes = eval_data.get("expected_outcomes", {})
            if outcomes.get("recommended_action"):
                expected.append(f"Recommended action: {outcomes['recommended_action']}")
            if outcomes.get("probability_of_success"):
                expected.append(f"Success probability: {outcomes['probability_of_success']:.0%}")
        if not expected:
            expected.append("Expected to improve engagement")
        return expected

    def _explain_confidence(self, data: Dict, eval_data: Optional[Dict]) -> str:
        conf = data.get("confidence", 0)
        if conf > 0.8:
            return f"High confidence ({conf:.0%}) based on strong multi-source evidence"
        if conf > 0.6:
            return f"Moderate confidence ({conf:.0%}) — some uncertainty in input signals"
        return f"Low confidence ({conf:.0%}) — recommend gathering more data before execution"

    def _assemble_full_text(self, exp: StrategyExplanation) -> str:
        parts = [f"## Strategy: {exp.summary}\n"]
        parts.append("### Why This Strategy:")
        for w in exp.why_this:
            parts.append(f"- {w}")
        if exp.risks:
            parts.append("\n### Risks:")
            for r in exp.risks:
                parts.append(f"- {r}")
        parts.append("\n### Expected Results:")
        for e in exp.expected_results:
            parts.append(f"- {e}")
        parts.append(f"\n### Confidence: {exp.confidence_explanation}")
        return "\n".join(parts)
