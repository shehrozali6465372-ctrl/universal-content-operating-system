"""HallucinationDetector — detect AI hallucinations and fabricated content."""
from __future__ import annotations
from typing import List
from .models import EvalResult, EvalType

class HallucinationDetector:
    HALLUCINATION_SIGNALS = [
        "according to my training", "I believe", "it is said",
        "some sources suggest", "reportedly", "it is said that",
    ]
    def __init__(self, sensitivity: float = 0.5) -> None:
        self.sensitivity = sensitivity; self._results: List[EvalResult] = []
    def check(self, content: str) -> EvalResult:
        signals_found = [s for s in self.HALLUCINATION_SIGNALS if s.lower() in content.lower()]
        hallucination_rate = len(signals_found) / max(len(content.split()), 1) * 100
        score = max(0.0, 1.0 - hallucination_rate * self.sensitivity)
        result = EvalResult(eval_type=EvalType.HALLUCINATION, score=score, passed=score >= 0.5)
        result.details["signals"] = signals_found
        result.details["hallucination_rate"] = hallucination_rate
        if signals_found: result.issues.append(f"Found {len(signals_found)} hallucination signals")
        self._results.append(result); return result
    def get_results(self) -> List[EvalResult]:
        return list(self._results)
