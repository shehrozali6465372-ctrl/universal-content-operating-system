"""DecisionReasoner — structured decision-making with scoring and tradeoffs."""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from .models import ReasoningChain, ReasoningStep, ReasoningResult, ReasoningType


class DecisionReasoner:
    """Structured decision-making with scoring and tradeoff analysis."""

    def __init__(self) -> None:
        self._history: List[Dict[str, Any]] = []

    def decide(self, options: List[str], criteria: Optional[Dict[str, float]] = None,
               scores: Optional[Dict[str, Dict[str, float]]] = None) -> ReasoningResult:
        start = time.time()
        chain = ReasoningChain(reasoning_type=ReasoningType.DECISION)
        criteria = criteria or {"impact": 0.3, "feasibility": 0.3, "risk": 0.2, "cost": 0.2}

        chain.add_step(ReasoningStep(step_type="options", content=f"Evaluating {len(options)} options"))
        chain.add_step(ReasoningStep(step_type="criteria", content=str(list(criteria.keys()))))

        best_option = options[0] if options else "no_option"
        best_score = 0.0
        for opt in options:
            opt_scores = scores.get(opt, {}) if scores else {}
            total = sum(opt_scores.get(c, 0.5) * w for c, w in criteria.items())
            chain.add_step(ReasoningStep(step_type="scoring",
                content=f"{opt}: {total:.2f}", confidence=total))
            if total > best_score:
                best_score = total
                best_option = opt

        chain.conclusion = f"Selected: {best_option} (score: {best_score:.2f})"
        chain.confidence = best_score
        elapsed = (time.time() - start) * 1000
        result = ReasoningResult(chain=chain, answer=chain.conclusion,
                                 confidence=chain.confidence, reasoning_time_ms=elapsed)
        self._history.append(result.to_dict())
        return result

    def tradeoff_analysis(self, option_a: str, option_b: str,
                          factors: Optional[List[str]] = None) -> ReasoningResult:
        start = time.time()
        chain = ReasoningChain(reasoning_type=ReasoningType.DECISION)
        factors = factors or ["speed", "quality", "cost"]
        for f in factors:
            chain.add_step(ReasoningStep(step_type="factor", content=f"Comparing {f}"))
        chain.conclusion = f"Tradeoff analysis of {option_a} vs {option_b}"
        chain.confidence = 0.65
        elapsed = (time.time() - start) * 1000
        return ReasoningResult(chain=chain, answer=chain.conclusion,
                               confidence=chain.confidence, reasoning_time_ms=elapsed)

    def get_history(self) -> List[Dict[str, Any]]:
        return list(self._history)
