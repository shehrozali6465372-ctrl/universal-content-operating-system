"""MetaReasoner — reason about reasoning itself."""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from .models import ReasoningChain, ReasoningStep, ReasoningResult, ReasoningType


class MetaReasoner:
    """Reason about reasoning itself — meta-cognition."""

    def __init__(self) -> None:
        self._history: List[Dict[str, Any]] = []

    def evaluate_strategy(self, strategy: str, results: List[Dict[str, Any]]) -> ReasoningResult:
        start = time.time()
        chain = ReasoningChain(reasoning_type=ReasoningType.SELF_CRITIQUE)
        chain.add_step(ReasoningStep(step_type="strategy", content=strategy))
        success_count = sum(1 for r in results if r.get("success", False))
        ratio = success_count / max(len(results), 1)
        chain.add_step(ReasoningStep(step_type="evaluation",
            content=f"Success rate: {ratio:.1%} across {len(results)} results"))
        chain.conclusion = f"Strategy '{strategy}' effectiveness: {ratio:.1%}"
        chain.confidence = ratio
        elapsed = (time.time() - start) * 1000
        result = ReasoningResult(chain=chain, answer=chain.conclusion,
                                 confidence=chain.confidence, reasoning_time_ms=elapsed)
        self._history.append(result.to_dict())
        return result

    def suggest_improvement(self, current_approach: str,
                            issues: Optional[List[str]] = None) -> ReasoningResult:
        start = time.time()
        chain = ReasoningChain(reasoning_type=ReasoningType.SELF_CRITIQUE)
        chain.add_step(ReasoningStep(step_type="current", content=current_approach))
        for issue in (issues or []):
            chain.add_step(ReasoningStep(step_type="issue", content=issue))
        chain.conclusion = f"Improvement suggested for: {current_approach}"
        chain.confidence = 0.65
        elapsed = (time.time() - start) * 1000
        return ReasoningResult(chain=chain, answer=chain.conclusion,
                               confidence=chain.confidence, reasoning_time_ms=elapsed)

    def get_history(self) -> List[Dict[str, Any]]:
        return list(self._history)
