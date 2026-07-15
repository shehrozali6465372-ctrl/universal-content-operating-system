"""Risk Analyzer — Risk-aware strategy selection."""
from __future__ import annotations
from typing import Any, Dict, List, Optional


class RiskAssessment:
    """Risk assessment for a strategy."""
    __slots__ = ("strategy_id", "overall_risk", "risk_score", "risk_factors",
                 "mitigations", "risk_level", "confidence_impact")

    def __init__(self, strategy_id: str = "") -> None:
        self.strategy_id = strategy_id
        self.overall_risk = 0.0
        self.risk_score = 0.0
        self.risk_factors: List[Dict[str, Any]] = []
        self.mitigations: List[Dict[str, str]] = []
        self.risk_level = "medium"
        self.confidence_impact = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "strategy_id": self.strategy_id,
            "overall_risk": round(self.overall_risk, 3),
            "risk_level": self.risk_level,
            "risk_factors": self.risk_factors,
            "mitigations": self.mitigations,
            "confidence_impact": round(self.confidence_impact, 4),
        }


class RiskAnalyzer:
    """Analyzes risks across strategy dimensions."""

    RISK_FACTORS = {
        "competition_level": {"threshold_high": 0.8, "threshold_medium": 0.5, "weight": 0.25},
        "trend_volatility": {"threshold_high": 0.7, "threshold_medium": 0.4, "weight": 0.2},
        "content_quality": {"threshold_high": 0.9, "threshold_medium": 0.6, "weight": 0.2, "inverse": True},
        "audience_fit": {"threshold_high": 0.9, "threshold_medium": 0.6, "weight": 0.15, "inverse": True},
        "topic_saturation": {"threshold_high": 0.8, "threshold_medium": 0.5, "weight": 0.15},
        "confidence_level": {"threshold_high": 0.9, "threshold_medium": 0.6, "weight": 0.05, "inverse": True},
    }

    def __init__(self) -> None:
        pass

    def assess(self, strategy_data: Dict[str, Any]) -> RiskAssessment:
        """Assess risk for a strategy."""
        result = RiskAssessment(strategy_id=strategy_data.get("strategy_id", ""))
        total_risk = 0.0

        for factor_name, config in self.RISK_FACTORS.items():
            value = strategy_data.get(factor_name, 0.5)
            inverse = config.get("inverse", False)
            risk_value = (1.0 - value) if inverse else value
            weight = config["weight"]
            total_risk += risk_value * weight

            if risk_value > config["threshold_high"]:
                level = "high"
            elif risk_value > config["threshold_medium"]:
                level = "medium"
            else:
                level = "low"

            result.risk_factors.append({
                "factor": factor_name,
                "value": round(value, 3),
                "risk": round(risk_value, 3),
                "level": level,
            })

        result.overall_risk = round(total_risk, 3)
        result.risk_level = self._classify_risk(total_risk)
        result.risk_score = round(total_risk * 100, 1)
        result.mitigations = self._suggest_mitigations(result.risk_factors)
        result.confidence_impact = round(-total_risk * 0.2, 4)

        return result

    def compare_risks(self, assessments: List[RiskAssessment]) -> List[RiskAssessment]:
        """Sort assessments by risk (lowest first)."""
        return sorted(assessments, key=lambda a: a.overall_risk)

    def suggest_low_risk_strategy(self, strategies: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Pick the strategy with lowest risk."""
        if not strategies:
            return None
        assessments = [(self.assess(s), s) for s in strategies]
        assessments.sort(key=lambda x: x[0].overall_risk)
        return assessments[0][1]

    def _classify_risk(self, score: float) -> str:
        if score < 0.3:
            return "low"
        if score < 0.6:
            return "medium"
        return "high"

    def _suggest_mitigations(self, factors: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        mitigations: List[Dict[str, str]] = []
        for f in factors:
            if f["level"] == "high":
                name = f["factor"]
                if name == "competition_level":
                    mitigations.append({"factor": name, "action": "Differentiate with unique angle"})
                elif name == "trend_volatility":
                    mitigations.append({"factor": name, "action": "Wait for trend stabilization"})
                elif name == "content_quality":
                    mitigations.append({"factor": name, "action": "Enhance content quality before publishing"})
                elif name == "topic_saturation":
                    mitigations.append({"factor": name, "action": "Find sub-niche within topic"})
                elif name == "confidence_level":
                    mitigations.append({"factor": name, "action": "Gather more evidence before decision"})
                else:
                    mitigations.append({"factor": name, "action": "Review and reduce exposure"})
        return mitigations
