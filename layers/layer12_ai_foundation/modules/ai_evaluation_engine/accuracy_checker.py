"""AccuracyChecker — evaluate content accuracy."""
from __future__ import annotations
import re
from typing import List
from .models import EvalResult, EvalType

class AccuracyChecker:
    def __init__(self, min_accuracy: float = 0.6) -> None:
        self.min_accuracy = min_accuracy; self._results: List[EvalResult] = []
    def check(self, content: str, reference: str = "") -> EvalResult:
        score = self._calculate(content, reference)
        result = EvalResult(eval_type=EvalType.ACCURACY, score=score, passed=score >= self.min_accuracy)
        if not result.passed: result.issues.append(f"Accuracy {score:.2f} below threshold")
        self._results.append(result); return result
    @staticmethod
    def _calculate(content: str, reference: str) -> float:
        if not reference:
            score = 0.7
            if re.search(r"\d{4}", content): score += 0.1
            if len(content.split()) > 10: score += 0.1
            return min(1.0, score)
        content_words = set(content.lower().split())
        ref_words = set(reference.lower().split())
        if not ref_words: return 0.5
        return len(content_words & ref_words) / len(ref_words)
    def get_results(self) -> List[EvalResult]:
        return list(self._results)
