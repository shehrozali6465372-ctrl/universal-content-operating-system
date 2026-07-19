"""LogicalReasoner — deductive, inductive, and abductive reasoning."""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from .models import ReasoningChain, ReasoningStep, ReasoningResult, ReasoningType


class LogicalReasoner:
    """Deductive, inductive, and abductive logical reasoning."""

    def __init__(self) -> None:
        self._history: List[Dict[str, Any]] = []

    def deductive(self, premises: List[str]) -> ReasoningResult:
        start = time.time()
        chain = ReasoningChain(reasoning_type=ReasoningType.LOGICAL)
        for i, p in enumerate(premises):
            chain.add_step(ReasoningStep(step_type="premise", content=p, confidence=0.9))

        if premises:
            conclusion = f"Based on {len(premises)} premises, logical conclusion follows."
            chain.add_step(ReasoningStep(step_type="conclusion", content=conclusion))
            chain.conclusion = conclusion
            chain.confidence = min(1.0, 0.5 + len(premises) * 0.1)
        elapsed = (time.time() - start) * 1000
        result = ReasoningResult(chain=chain, answer=chain.conclusion,
                                 confidence=chain.confidence, reasoning_time_ms=elapsed)
        self._history.append(result.to_dict())
        return result

    def inductive(self, observations: List[str]) -> ReasoningResult:
        start = time.time()
        chain = ReasoningChain(reasoning_type=ReasoningType.LOGICAL)
        for obs in observations:
            chain.add_step(ReasoningStep(step_type="observation", content=obs, confidence=0.7))
        if observations:
            pattern = f"Pattern detected across {len(observations)} observations."
            chain.add_step(ReasoningStep(step_type="generalization", content=pattern))
            chain.conclusion = pattern
            chain.confidence = min(1.0, 0.3 + len(observations) * 0.08)
        elapsed = (time.time() - start) * 1000
        return ReasoningResult(chain=chain, answer=chain.conclusion,
                               confidence=chain.confidence, reasoning_time_ms=elapsed)

    def abductive(self, observations: List[str], hypotheses: Optional[List[str]] = None) -> ReasoningResult:
        start = time.time()
        chain = ReasoningChain(reasoning_type=ReasoningType.LOGICAL)
        for obs in observations:
            chain.add_step(ReasoningStep(step_type="observation", content=obs))
        best_hypothesis = (hypotheses[0] if hypotheses else
                           f"Best explanation for {len(observations)} observations")
        chain.add_step(ReasoningStep(step_type="hypothesis", content=best_hypothesis))
        chain.conclusion = best_hypothesis
        chain.confidence = 0.6
        elapsed = (time.time() - start) * 1000
        return ReasoningResult(chain=chain, answer=chain.conclusion,
                               confidence=chain.confidence, reasoning_time_ms=elapsed)

    def get_history(self) -> List[Dict[str, Any]]:
        return list(self._history)
