"""Decision Engine — Make publish decisions based on quality scores."""
from __future__ import annotations
from typing import Dict, List

from layers.layer06_quality.modules.quality_scoring_engine.quality_result import ModuleScore


# Decision thresholds
APPROVE_THRESHOLD = 80
APPROVE_WITH_WARNINGS_THRESHOLD = 65
HUMAN_REVIEW_THRESHOLD = 50
REVISE_THRESHOLD = 35

# Hard-stop conditions (any triggers direct REJECT or HUMAN_REVIEW)
HARD_STOP_RULES = {
    "safety_critical": {"module": "safety", "max_score": 30},
    "fact_validation_fail": {"module": "fact_validation", "max_score": 20},
    "platform_compliance_fail": {"module": "platform_compliance", "max_score": 30},
}


class DecisionResult:
    """Decision output."""

    __slots__ = ("decision", "reason", "hard_stops_triggered", "module_contributions")

    def __init__(self, decision: str = "reject", reason: str = "") -> None:
        self.decision = decision
        self.reason = reason
        self.hard_stops_triggered: List[str] = []
        self.module_contributions: Dict[str, str] = {}

    def to_dict(self) -> dict:
        return {
            "decision": self.decision,
            "reason": self.reason,
            "hard_stops": self.hard_stops_triggered,
            "module_contributions": self.module_contributions,
        }


class DecisionEngine:
    """Make publish decisions based on quality analysis."""

    def __init__(self) -> None:
        self._decision_count = 0

    def decide(
        self,
        overall_score: float,
        module_scores: List[ModuleScore],
        confidence: float = 0.5,
    ) -> DecisionResult:
        """Make a publish decision."""
        result = DecisionResult()
        hard_stops = self._check_hard_stops(module_scores)

        if hard_stops:
            result.decision = "reject"
            result.hard_stops_triggered = hard_stops
            result.reason = f"Hard stops triggered: {', '.join(hard_stops)}"
            self._decision_count += 1
            return result

        # Score-based decision
        if overall_score >= APPROVE_THRESHOLD and confidence >= 0.7:
            result.decision = "approve"
            result.reason = f"High quality ({overall_score:.1f}) with sufficient confidence ({confidence:.0%})"
        elif overall_score >= APPROVE_WITH_WARNINGS_THRESHOLD:
            result.decision = "approve_with_warnings"
            result.reason = f"Acceptable quality ({overall_score:.1f}) but has warnings"
        elif overall_score >= HUMAN_REVIEW_THRESHOLD:
            result.decision = "human_review"
            result.reason = f"Moderate quality ({overall_score:.1f}) — human review recommended"
        elif overall_score >= REVISE_THRESHOLD:
            result.decision = "revise"
            result.reason = f"Below threshold ({overall_score:.1f}) — revision needed"
        else:
            result.decision = "reject"
            result.reason = f"Quality too low ({overall_score:.1f})"

        # Module contributions
        for ms in module_scores:
            if ms.score >= 85:
                result.module_contributions[ms.module_name] = "positive"
            elif ms.score >= 60:
                result.module_contributions[ms.module_name] = "neutral"
            else:
                result.module_contributions[ms.module_name] = "negative"

        self._decision_count += 1
        return result

    def _check_hard_stops(self, module_scores: List[ModuleScore]) -> List[str]:
        """Check for hard-stop violations."""
        triggered = []
        for stop_name, rule in HARD_STOP_RULES.items():
            for ms in module_scores:
                if ms.module_name == rule["module"] and ms.score <= rule["max_score"]:
                    triggered.append(stop_name)
        return triggered

    @property
    def decision_count(self) -> int:
        return self._decision_count
