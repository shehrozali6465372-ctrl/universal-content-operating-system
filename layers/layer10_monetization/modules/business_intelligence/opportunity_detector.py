"""OpportunityDetector — validated, explicitly sourced opportunity records."""
from __future__ import annotations
import itertools
import time
from typing import Any, Dict, List

_OD_COUNTER = itertools.count(1)
OPPORTUNITY_TYPES = ("trending_niche", "new_platform", "viral_opportunity",
                     "sponsorship", "affiliate", "premium_product", "course",
                     "consulting", "partnership", "other")


class Opportunity:
    def __init__(self, opportunity_type: str = "other", title: str = "") -> None:
        self.opportunity_id = f"opp_{next(_OD_COUNTER)}"
        self.opportunity_type = opportunity_type if opportunity_type in OPPORTUNITY_TYPES else "other"
        self.title = title
        self.description = ""
        self.platform = ""
        self.estimated_revenue = 0.0
        self.confidence = 0.0
        self.priority = 2
        self.status = "detected"
        self.detected_at = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {"opportunity_id": self.opportunity_id, "type": self.opportunity_type,
                "title": self.title, "estimated_revenue": round(self.estimated_revenue, 2),
                "confidence": round(self.confidence, 3), "platform": self.platform,
                "status": self.status}


class OpportunityDetector:
    def __init__(self, max_entries: int = 10000) -> None:
        if max_entries <= 0:
            raise ValueError("max_entries must be positive")
        self._max_entries = max_entries
        self._opportunities: List[Opportunity] = []

    def detect(self, opportunity_type: str, title: str, platform: str = "",
               estimated_revenue: float = 0.0, confidence: float = 0.5,
               description: str = "") -> Opportunity:
        if estimated_revenue < 0 or not 0 <= confidence <= 1:
            raise ValueError("invalid opportunity estimate or confidence")
        opportunity = Opportunity(opportunity_type, title)
        opportunity.platform, opportunity.estimated_revenue = platform, estimated_revenue
        opportunity.confidence, opportunity.description = confidence, description
        self._opportunities.append(opportunity)
        if len(self._opportunities) > self._max_entries:
            del self._opportunities[:-self._max_entries]
        return opportunity

    def get_top_opportunities(self, count: int = 5, platform: str = "") -> List[Opportunity]:
        opportunities = self._opportunities if not platform else [
            item for item in self._opportunities if item.platform == platform
        ]
        return sorted(opportunities, key=lambda item: item.estimated_revenue * item.confidence,
                      reverse=True)[:max(0, count)]

    def get_by_type(self, opportunity_type: str) -> List[Opportunity]:
        return [item for item in self._opportunities if item.opportunity_type == opportunity_type]

    def get_by_platform(self, platform: str) -> List[Opportunity]:
        return [item for item in self._opportunities if item.platform == platform]

    def mark_accepted(self, opportunity_id: str) -> bool:
        opportunity = next((item for item in self._opportunities if item.opportunity_id == opportunity_id), None)
        if opportunity is None:
            return False
        opportunity.status = "accepted"
        return True

    def mark_rejected(self, opportunity_id: str) -> bool:
        opportunity = next((item for item in self._opportunities if item.opportunity_id == opportunity_id), None)
        if opportunity is None:
            return False
        opportunity.status = "rejected"
        return True

    def get_pending(self) -> List[Opportunity]:
        return [item for item in self._opportunities if item.status == "detected"]

    def get_total_estimated_revenue(self, platform: str = "") -> float:
        return round(sum(item.estimated_revenue for item in self._opportunities
                         if not platform or item.platform == platform), 2)

    def get_stats(self) -> Dict[str, Any]:
        types: Dict[str, int] = {}
        statuses: Dict[str, int] = {}
        for opportunity in self._opportunities:
            types[opportunity.opportunity_type] = types.get(opportunity.opportunity_type, 0) + 1
            statuses[opportunity.status] = statuses.get(opportunity.status, 0) + 1
        return {"total": len(self._opportunities), "by_type": types,
                "by_status": statuses, "total_estimated_revenue": self.get_total_estimated_revenue()}
