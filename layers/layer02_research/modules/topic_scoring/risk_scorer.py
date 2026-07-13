"""
Risk Scorer
Layer 2: Research Engine — Module 8

Assesses risk levels for topic decisions:
- Competition risk
- Trend volatility risk
- Knowledge gap risk
- Audience risk
- Overall risk classification
"""

from typing import List


RISK_LEVELS = ["VERY_LOW", "LOW", "MEDIUM", "HIGH", "CRITICAL"]


class RiskAssessment:
    """Risk assessment result."""

    __slots__ = ("competition_risk", "trend_risk", "knowledge_risk",
                 "audience_risk", "overall_risk", "risk_level",
                 "risk_factors", "mitigations")

    def __init__(self):
        self.competition_risk = 0.0
        self.trend_risk = 0.0
        self.knowledge_risk = 0.0
        self.audience_risk = 0.0
        self.overall_risk = 0.0
        self.risk_level = "MEDIUM"
        self.risk_factors: List[str] = []
        self.mitigations: List[str] = []

    def to_dict(self) -> dict:
        return {
            "competition_risk": self.competition_risk,
            "trend_risk": self.trend_risk,
            "knowledge_risk": self.knowledge_risk,
            "audience_risk": self.audience_risk,
            "overall_risk": self.overall_risk,
            "risk_level": self.risk_level,
            "risk_factors": self.risk_factors,
            "mitigations": self.mitigations,
        }


class RiskScorer:
    """Assess risk for topic decisions."""

    def calculate(
        self,
        trend_score: float = 5.0,
        competition_score: float = 5.0,
        knowledge_score: float = 5.0,
        audience_score: float = 5.0,
        verification_score: float = 5.0,
    ) -> RiskAssessment:
        result = RiskAssessment()
        factors = []
        mitigations = []

        # Competition risk: high competition = high risk
        result.competition_risk = round(competition_score / 10.0, 3)
        if competition_score >= 8.0:
            factors.append("Very high competition")
            mitigations.append("Focus on long-tail sub-niches")

        # Trend risk: low trend = high risk (topic may be dying)
        result.trend_risk = round(max(0, (10 - trend_score) / 10.0), 3)
        if trend_score <= 3.0:
            factors.append("Trend is declining or weak")
            mitigations.append("Verify trend with multiple sources")

        # Knowledge risk: low knowledge = high risk
        result.knowledge_risk = round(max(0, (10 - knowledge_score) / 10.0), 3)
        if knowledge_score <= 3.0:
            factors.append("Insufficient knowledge base")
            mitigations.append("Research more before publishing")

        # Audience risk: low audience = high risk
        result.audience_risk = round(max(0, (10 - audience_score) / 10.0), 3)
        if audience_score <= 3.0:
            factors.append("Weak audience alignment")
            mitigations.append("Target a different audience segment")

        # Overall risk (average)
        result.overall_risk = round(
            (result.competition_risk + result.trend_risk +
             result.knowledge_risk + result.audience_risk) / 4, 3
        )

        # Risk level classification
        if result.overall_risk <= 0.2:
            result.risk_level = "VERY_LOW"
        elif result.overall_risk <= 0.4:
            result.risk_level = "LOW"
        elif result.overall_risk <= 0.6:
            result.risk_level = "MEDIUM"
        elif result.overall_risk <= 0.8:
            result.risk_level = "HIGH"
        else:
            result.risk_level = "CRITICAL"

        # Low verification is always a risk
        if verification_score <= 3.0:
            factors.append("Low verification confidence")
            mitigations.append("Verify claims with additional sources")

        result.risk_factors = factors
        result.mitigations = mitigations
        return result
