"""QualityChecker — evaluate content quality score."""
from __future__ import annotations
from typing import List
from .models import EvalResult, EvalType

class QualityChecker:
    def __init__(self, min_score: float = 0.5) -> None:
        self.min_score = min_score; self._results: List[EvalResult] = []
    def check(self, content: str) -> EvalResult:
        score = self._calculate_score(content)
        result = EvalResult(eval_type=EvalType.QUALITY, score=score, passed=score >= self.min_score)
        if not result.passed: result.issues.append(f"Quality {score:.2f} below threshold {self.min_score}")
        self._results.append(result); return result
    @staticmethod
    def _calculate_score(content: str) -> float:
        words = content.split()
        score = 0.5
        if len(words) > 20: score += 0.1
        if len(words) > 50: score += 0.1
        unique_ratio = len(set(w.lower() for w in words)) / max(len(words), 1)
        score += unique_ratio * 0.2
        return min(1.0, score)
    def get_results(self) -> List[EvalResult]:
        return list(self._results)
