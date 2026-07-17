"""OpportunityDetector — Detect growth and viral opportunities."""
from __future__ import annotations
import itertools
import time
from typing import Any, Dict, List, Optional

_OD_COUNTER = itertools.count(1)


class Opportunity:
    """A detected growth opportunity."""

    __slots__ = ("opportunity_id", "type", "description", "platform",
                 "estimated_impact", "confidence", "detected_at")

    def __init__(self, opp_type: str = "", description: str = "") -> None:
        self.opportunity_id: str = f"opp_{next(_OD_COUNTER)}"
        self.type = opp_type
        self.description = description
        self.platform: str = ""
        self.estimated_impact: float = 0.5
        self.confidence: float = 0.5
        self.detected_at: float = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "opportunity_id": self.opportunity_id, "type": self.type,
            "platform": self.platform, "impact": self.estimated_impact,
        }


class OpportunityDetector:
    """Detect trending topics, viral opportunities, and growth gaps."""

    def __init__(self) -> None:
        self._opportunities: List[Opportunity] = []

    def scan(self, context: Optional[Dict[str, Any]] = None) -> List[Opportunity]:
        context = context or {}
        detected = []

        trend = Opportunity("trending", "AI content trending on social media")
        trend.platform = context.get("platform", "universal")
        trend.estimated_impact = 0.7
        trend.confidence = 0.6
        self._opportunities.append(trend)
        detected.append(trend)

        if context.get("platform") in ("tiktok", "instagram"):
            viral = Opportunity("viral", "Short-form video opportunity detected")
            viral.platform = context["platform"]
            viral.estimated_impact = 0.8
            viral.confidence = 0.5
            self._opportunities.append(viral)
            detected.append(viral)

        gap = Opportunity("market_gap", "Underserved niche in educational content")
        gap.platform = "universal"
        gap.estimated_impact = 0.6
        gap.confidence = 0.4
        self._opportunities.append(gap)
        detected.append(gap)

        return detected

    def get_opportunities(self, opp_type: str = "",
                          min_impact: float = 0.0) -> List[Opportunity]:
        results = self._opportunities
        if opp_type:
            results = [o for o in results if o.type == opp_type]
        if min_impact > 0:
            results = [o for o in results if o.estimated_impact >= min_impact]
        return results

    def get_top_opportunities(self, count: int = 3) -> List[Opportunity]:
        return sorted(self._opportunities, key=lambda o: o.estimated_impact, reverse=True)[:count]

    def get_stats(self) -> Dict[str, Any]:
        types = {}
        for o in self._opportunities:
            types[o.type] = types.get(o.type, 0) + 1
        return {"total": len(self._opportunities), "by_type": types}
