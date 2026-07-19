"""ReasoningEnsemble — combine multiple reasoning approaches."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .models import ReasoningResult


class ReasoningEnsemble:
    """Combine results from multiple reasoning approaches."""

    def __init__(self) -> None:
        self._history: List[Dict[str, Any]] = []

    def ensemble(self, results: List[ReasoningResult],
                 weights: Optional[Dict[str, float]] = None) -> ReasoningResult:
        if not results:
            return ReasoningResult(answer="", confidence=0.0)

        best = max(results, key=lambda r: r.confidence)
        avg_confidence = sum(r.confidence for r in results) / len(results)

        return ReasoningResult(
            chain=best.chain, answer=best.answer,
            confidence=avg_confidence,
            alternatives=[r.answer for r in results if r.answer != best.answer],
            reasoning_time_ms=sum(r.reasoning_time_ms for r in results),
        )

    def voting(self, results: List[ReasoningResult]) -> ReasoningResult:
        if not results:
            return ReasoningResult(answer="", confidence=0.0)
        answer_counts: Dict[str, int] = {}
        for r in results:
            answer_counts[r.answer] = answer_counts.get(r.answer, 0) + 1
        best_answer = max(answer_counts, key=answer_counts.get)
        confidence = answer_counts[best_answer] / len(results)
        return ReasoningResult(answer=best_answer, confidence=confidence)
