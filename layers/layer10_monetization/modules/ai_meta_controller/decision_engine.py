"""Decision Engine — AI decision center."""
from __future__ import annotations
import itertools
import time
from typing import Any, Dict, List, Optional

_DE_COUNTER = itertools.count(1)

DECISIONS = ("publish_now", "wait", "revise", "generate_image", "rewrite",
             "research_more", "retry", "rollback", "human_review", "reject")


class Decision:
    """An AI decision."""

    __slots__ = ("decision_id", "action", "confidence", "reason",
                 "risk_level", "context", "timestamp", "outcome")

    def __init__(self, action: str = "", confidence: float = 0.5) -> None:
        self.decision_id: str = f"dec_{next(_DE_COUNTER)}"
        self.action = action
        self.confidence = confidence
        self.reason: str = ""
        self.risk_level: str = "low"
        self.context: Dict[str, Any] = {}
        self.timestamp: float = time.time()
        self.outcome: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision_id": self.decision_id, "action": self.action,
            "confidence": round(self.confidence, 3), "risk_level": self.risk_level,
        }


class DecisionEngine:
    """Make AI decisions based on confidence, risk, and context."""

    def __init__(self) -> None:
        self._decisions: List[Decision] = []
        self._rules: Dict[str, float] = {
            "publish_now": 0.8, "wait": 0.5, "revise": 0.6,
            "rewrite": 0.7, "reject": 0.9, "human_review": 0.4,
        }

    def decide(self, context: Dict[str, Any]) -> Decision:
        quality_score = context.get("quality_score", 0.5)
        risk_level = context.get("risk_level", "low")
        has_conflicts = context.get("has_conflicts", False)

        if quality_score >= 0.8 and risk_level == "low" and not has_conflicts:
            action, confidence = "publish_now", min(1.0, quality_score + 0.1)
        elif quality_score < 0.5:
            action, confidence = "rewrite", 0.7
        elif has_conflicts:
            action, confidence = "human_review", 0.5
        elif risk_level == "high":
            action, confidence = "wait", 0.6
        else:
            action, confidence = "revise", 0.6

        decision = Decision(action, confidence)
        decision.risk_level = risk_level
        decision.context = dict(context)
        self._decisions.append(decision)
        return decision

    def get_decision(self, decision_id: str) -> Optional[Decision]:
        for d in self._decisions:
            if d.decision_id == decision_id:
                return d
        return None

    def get_recent(self, limit: int = 10) -> List[Decision]:
        return self._decisions[-limit:]

    def get_accuracy(self) -> float:
        if not self._decisions:
            return 0.0
        correct = sum(1 for d in self._decisions if d.outcome == "correct")
        return round(correct / len(self._decisions), 3)
