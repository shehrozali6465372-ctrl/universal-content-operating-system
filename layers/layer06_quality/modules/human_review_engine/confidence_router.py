"""Confidence Router — Route content based on quality confidence scores."""
from __future__ import annotations
from typing import List

from layers.layer06_quality.modules.human_review_engine.review_models import (
    ReviewRequest,
)


AUTO_APPROVE_THRESHOLD = 0.9
MANUAL_REVIEW_THRESHOLD = 0.6
HIGH_RISK_CATEGORIES = {"legal", "financial", "medical", "political"}


class RoutingDecision:
    """A routing decision for content."""

    __slots__ = ("action", "reason", "confidence", "risk_category",
                 "requires_human", "escalation_level")

    def __init__(
        self,
        action: str = "review",
        reason: str = "",
        confidence: float = 0.5,
        risk_category: str = "normal",
    ) -> None:
        self.action = action
        self.reason = reason
        self.confidence = confidence
        self.risk_category = risk_category
        self.requires_human = True
        self.escalation_level = 0

    def to_dict(self) -> dict:
        return {
            "action": self.action,
            "reason": self.reason,
            "confidence": round(self.confidence, 3),
            "risk_category": self.risk_category,
            "requires_human": self.requires_human,
            "escalation_level": self.escalation_level,
        }


class ConfidenceRouter:
    """Route content for review based on confidence and risk."""

    def __init__(self) -> None:
        self._route_count = 0

    def route(self, request: ReviewRequest) -> RoutingDecision:
        """Route a review request based on confidence and risk."""
        decision = RoutingDecision(
            confidence=request.confidence_score,
            risk_category=request.risk_category,
        )

        # Risk override
        if request.risk_category in HIGH_RISK_CATEGORIES:
            decision.action = "escalate"
            decision.requires_human = True
            decision.escalation_level = 2
            decision.reason = f"High-risk category '{request.risk_category}' requires escalation"
            self._route_count += 1
            return decision

        # Confidence-based routing
        if request.confidence_score >= AUTO_APPROVE_THRESHOLD:
            decision.action = "auto_approve"
            decision.requires_human = False
            decision.reason = f"High confidence ({request.confidence_score:.0%}) — eligible for auto-approval"
        elif request.confidence_score >= MANUAL_REVIEW_THRESHOLD:
            decision.action = "review"
            decision.requires_human = True
            decision.reason = f"Moderate confidence ({request.confidence_score:.0%}) — standard review"
        else:
            decision.action = "escalate"
            decision.requires_human = True
            decision.escalation_level = 1
            decision.reason = f"Low confidence ({request.confidence_score:.0%}) — requires senior review"

        self._route_count += 1
        return decision

    def route_batch(self, requests: List[ReviewRequest]) -> List[RoutingDecision]:
        """Route multiple requests."""
        return [self.route(r) for r in requests]

    def get_auto_approvable(self, decisions: List[RoutingDecision]) -> List[RoutingDecision]:
        """Return decisions eligible for auto-approval."""
        return [d for d in decisions if d.action == "auto_approve"]

    @property
    def route_count(self) -> int:
        return self._route_count
