"""CounterfactualReasoner — explore 'what if' scenarios."""
from __future__ import annotations

import time
from typing import Any, Dict, List

from .models import ReasoningChain, ReasoningStep, ReasoningResult, ReasoningType


class CounterfactualReasoner:
    """Explore 'what if' scenarios and alternative outcomes."""

    def __init__(self) -> None:
        self._history: List[Dict[str, Any]] = []

    def what_if(self, scenario: str, change: str, expected_outcome: str = "") -> ReasoningResult:
        start = time.time()
        chain = ReasoningChain(reasoning_type=ReasoningType.LOGICAL)
        chain.add_step(ReasoningStep(step_type="baseline", content=scenario))
        chain.add_step(ReasoningStep(step_type="counterfactual", content=f"If {change}..."))
        outcome = expected_outcome or f"Under changed condition: {change}"
        chain.add_step(ReasoningStep(step_type="outcome", content=outcome))
        chain.conclusion = f"What if: {change} → {outcome}"
        chain.confidence = 0.6
        elapsed = (time.time() - start) * 1000
        result = ReasoningResult(chain=chain, answer=chain.conclusion,
                                 confidence=chain.confidence, reasoning_time_ms=elapsed)
        self._history.append(result.to_dict())
        return result

    def compare_paths(self, scenario: str, paths: List[str]) -> ReasoningResult:
        start = time.time()
        chain = ReasoningChain(reasoning_type=ReasoningType.STRATEGIC)
        for p in paths:
            chain.add_step(ReasoningStep(step_type="path", content=p))
        chain.conclusion = f"Compared {len(paths)} alternative paths"
        chain.confidence = 0.65
        elapsed = (time.time() - start) * 1000
        return ReasoningResult(chain=chain, answer=chain.conclusion,
                               confidence=chain.confidence, reasoning_time_ms=elapsed)

    def get_history(self) -> List[Dict[str, Any]]:
        return list(self._history)
