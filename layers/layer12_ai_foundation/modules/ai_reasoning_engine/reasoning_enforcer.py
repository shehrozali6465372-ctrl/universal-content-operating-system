"""ReasoningEnforcer — enforce reasoning quality and completeness."""
from __future__ import annotations

from typing import Any, Dict, List

from .models import ReasoningChain


class ReasoningEnforcer:
    """Enforce reasoning quality standards and completeness."""

    def __init__(self, min_steps: int = 2, min_confidence: float = 0.3,
                 require_conclusion: bool = True) -> None:
        self.min_steps = min_steps
        self.min_confidence = min_confidence
        self.require_conclusion = require_conclusion

    def enforce(self, chain: ReasoningChain) -> Dict[str, Any]:
        violations: List[str] = []
        if chain.step_count < self.min_steps:
            violations.append(f"Need at least {self.min_steps} steps")
        avg_conf = sum(s.confidence for s in chain.steps) / max(chain.step_count, 1)
        if avg_conf < self.min_confidence:
            violations.append(f"Average confidence {avg_conf:.2f} below threshold {self.min_confidence}")
        if self.require_conclusion and not chain.conclusion:
            violations.append("Conclusion required but missing")
        return {"passes": len(violations) == 0, "violations": violations}
