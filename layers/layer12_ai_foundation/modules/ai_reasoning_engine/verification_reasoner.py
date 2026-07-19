"""VerificationReasoner — verify reasoning chains for logical consistency."""
from __future__ import annotations

from typing import Any, Dict, List

from .models import ReasoningChain


class VerificationReasoner:
    """Verify reasoning chains for logical consistency and completeness."""

    def __init__(self) -> None:
        self._history: List[Dict[str, Any]] = []

    def verify(self, chain: ReasoningChain) -> Dict[str, Any]:
        issues: List[str] = []
        warnings: List[str] = []
        if chain.step_count == 0:
            issues.append("Empty reasoning chain")
        low_conf_steps = [s for s in chain.steps if s.confidence < 0.3]
        if low_conf_steps:
            warnings.append(f"{len(low_conf_steps)} steps with low confidence")
        if not chain.conclusion:
            issues.append("No conclusion reached")

        chain.is_valid = len(issues) == 0
        result = {"valid": chain.is_valid, "issues": issues, "warnings": warnings,
                  "step_count": chain.step_count, "avg_confidence": sum(
                      s.confidence for s in chain.steps) / max(chain.step_count, 1)}
        self._history.append(result)
        return result

    def cross_check(self, chains: List[ReasoningChain]) -> Dict[str, Any]:
        if not chains:
            return {"consistent": False, "reason": "no chains"}
        conclusions = [c.conclusion for c in chains if c.conclusion]
        unique = set(conclusions)
        consistency = 1.0 if len(unique) <= 1 else 0.5
        return {"consistent": consistency > 0.5, "unique_conclusions": len(unique),
                "consistency_score": consistency}

    def get_history(self) -> List[Dict[str, Any]]:
        return list(self._history)
