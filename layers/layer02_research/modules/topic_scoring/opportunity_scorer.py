"""
Opportunity Scorer
Layer 2: Research Engine — Module 8

Calculates opportunity scores for topics:
- Market opportunity (low competition + high demand)
- Content gap opportunity
- Timing opportunity
- Audience gap opportunity
"""

from typing import Dict


class OpportunityScore:
    """Computed opportunity assessment."""

    __slots__ = ("market_opportunity", "content_gap", "timing_opportunity",
                 "audience_gap", "overall_opportunity", "factors")

    def __init__(self):
        self.market_opportunity = 0.0
        self.content_gap = 0.0
        self.timing_opportunity = 0.0
        self.audience_gap = 0.0
        self.overall_opportunity = 0.0
        self.factors: Dict[str, float] = {}

    def to_dict(self) -> dict:
        return {
            "market_opportunity": self.market_opportunity,
            "content_gap": self.content_gap,
            "timing_opportunity": self.timing_opportunity,
            "audience_gap": self.audience_gap,
            "overall_opportunity": self.overall_opportunity,
            "factors": self.factors,
        }


class OpportunityScorer:
    """Calculate opportunity scores for topics."""

    def calculate(
        self,
        trend_score: float = 5.0,
        competition_score: float = 5.0,
        audience_score: float = 5.0,
        knowledge_score: float = 5.0,
        engagement_score: float = 5.0,
    ) -> OpportunityScore:
        """Calculate opportunity from module scores."""
        result = OpportunityScore()

        # Market opportunity: high trend + low competition = high opportunity
        result.market_opportunity = round(max(0, min(10,
            trend_score * 0.6 + (10 - competition_score) * 0.4
        )), 2)

        # Content gap: high knowledge + low competition = content gap
        result.content_gap = round(max(0, min(10,
            knowledge_score * 0.5 + (10 - competition_score) * 0.3 + audience_score * 0.2
        )), 2)

        # Timing opportunity: high trend + high engagement = good timing
        result.timing_opportunity = round(max(0, min(10,
            trend_score * 0.5 + engagement_score * 0.5
        )), 2)

        # Audience gap: high audience + low competition
        result.audience_gap = round(max(0, min(10,
            audience_score * 0.6 + (10 - competition_score) * 0.4
        )), 2)

        # Overall
        result.overall_opportunity = round(
            result.market_opportunity * 0.3 +
            result.content_gap * 0.25 +
            result.timing_opportunity * 0.25 +
            result.audience_gap * 0.2,
            2,
        )

        result.factors = {
            "trend_input": trend_score,
            "competition_input": competition_score,
            "audience_input": audience_score,
            "knowledge_input": knowledge_score,
            "engagement_input": engagement_score,
        }
        return result
