"""OpportunityDetector — Find trending niches, sponsorship, and affiliate opportunities."""
from __future__ import annotations
import itertools
import time
from typing import Any, Dict, List

_OD_COUNTER = itertools.count(1)

OPPORTUNITY_TYPES = (
    "trending_niche", "new_platform", "viral_opportunity",
    "sponsorship", "affiliate", "premium_product",
    "course", "consulting", "partnership", "other",
)


class Opportunity:
    """A detected business opportunity."""

    __slots__ = ("opportunity_id", "opportunity_type", "title", "description",
                 "platform", "estimated_revenue", "confidence",
                 "priority", "status", "detected_at")

    def __init__(self, opportunity_type: str = "other", title: str = "") -> None:
        self.opportunity_id: str = f"opp_{next(_OD_COUNTER)}"
        self.opportunity_type = opportunity_type if opportunity_type in OPPORTUNITY_TYPES else "other"
        self.title = title
        self.description: str = ""
        self.platform: str = ""
        self.estimated_revenue: float = 0.0
        self.confidence: float = 0.5
        self.priority: int = 2
        self.status: str = "detected"
        self.detected_at: float = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {"opportunity_id": self.opportunity_id, "type": self.opportunity_type,
                "title": self.title, "estimated_revenue": round(self.estimated_revenue, 2),
                "confidence": round(self.confidence, 3), "platform": self.platform}


class OpportunityDetector:
    """Detect trending niches, viral opportunities, sponsorships, and affiliate programs."""

    def __init__(self) -> None:
        self._opportunities: List[Opportunity] = []

    def detect(self, opportunity_type: str, title: str, platform: str = "",
               estimated_revenue: float = 0.0, confidence: float = 0.5,
               description: str = "") -> Opportunity:
        opp = Opportunity(opportunity_type, title)
        opp.platform = platform
        opp.estimated_revenue = estimated_revenue
        opp.confidence = confidence
        opp.description = description
        self._opportunities.append(opp)
        return opp

    def get_top_opportunities(self, count: int = 5,
                              platform: str = "") -> List[Opportunity]:
        opps = self._opportunities
        if platform:
            opps = [o for o in opps if o.platform == platform]
        return sorted(opps, key=lambda o: o.estimated_revenue * o.confidence,
                       reverse=True)[:count]

    def get_by_type(self, opportunity_type: str) -> List[Opportunity]:
        return [o for o in self._opportunities if o.opportunity_type == opportunity_type]

    def get_by_platform(self, platform: str) -> List[Opportunity]:
        return [o for o in self._opportunities if o.platform == platform]

    def mark_accepted(self, opportunity_id: str) -> bool:
        opp = next((o for o in self._opportunities if o.opportunity_id == opportunity_id), None)
        if opp:
            opp.status = "accepted"
            return True
        return False

    def mark_rejected(self, opportunity_id: str) -> bool:
        opp = next((o for o in self._opportunities if o.opportunity_id == opportunity_id), None)
        if opp:
            opp.status = "rejected"
            return True
        return False

    def get_pending(self) -> List[Opportunity]:
        return [o for o in self._opportunities if o.status == "detected"]

    def get_total_estimated_revenue(self, platform: str = "") -> float:
        opps = self._opportunities
        if platform:
            opps = [o for o in opps if o.platform == platform]
        return round(sum(o.estimated_revenue for o in opps), 2)

    def get_stats(self) -> Dict[str, Any]:
        types: Dict[str, int] = {}
        statuses: Dict[str, int] = {}
        for o in self._opportunities:
            types[o.opportunity_type] = types.get(o.opportunity_type, 0) + 1
            statuses[o.status] = statuses.get(o.status, 0) + 1
        return {"total": len(self._opportunities), "by_type": types,
                "by_status": statuses,
                "total_estimated_revenue": self.get_total_estimated_revenue()}
