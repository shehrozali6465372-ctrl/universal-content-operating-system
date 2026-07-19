"""ChainValidator — validate reasoning chains for completeness."""
from __future__ import annotations

from typing import Any, Dict, List

from .models import ReasoningChain


class ChainValidator:
    """Validate reasoning chains for completeness and quality."""

    MIN_STEPS = 2
    MIN_CONFIDENCE = 0.3

    def validate(self, chain: ReasoningChain) -> Dict[str, Any]:
        issues: List[str] = []
        if chain.step_count < self.MIN_STEPS:
            issues.append(f"Too few steps: {chain.step_count} < {self.MIN_STEPS}")
        if not chain.conclusion:
            issues.append("Missing conclusion")
        avg_conf = sum(s.confidence for s in chain.steps) / max(chain.step_count, 1)
        if avg_conf < self.MIN_CONFIDENCE:
            issues.append(f"Average confidence too low: {avg_conf:.2f}")
        has_premise = any(s.step_type in ("premise", "observation") for s in chain.steps)
        if not has_premise:
            issues.append("No premise or observation found")
        has_conclusion = any(s.step_type == "conclusion" for s in chain.steps) or bool(chain.conclusion)
        if not has_conclusion:
            issues.append("No conclusion step found")
        return {"valid": len(issues) == 0, "issues": issues,
                "step_count": chain.step_count, "avg_confidence": round(avg_conf, 4)}
