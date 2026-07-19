"""BiasDetector — detect content bias and unfair language."""
from __future__ import annotations
from typing import List
from .models import EvalResult, EvalType

class BiasDetector:
    BIAS_SIGNALS = ["always", "never", "all", "every", "only", "obviously", "clearly", "definitely"]
    def __init__(self) -> None:
        self._results: List[EvalResult] = []
    def check(self, content: str) -> EvalResult:
        words = content.lower().split()
        bias_count = sum(1 for w in words if w in self.BIAS_SIGNALS)
        bias_rate = bias_count / max(len(words), 1)
        score = max(0.0, 1.0 - bias_rate * 5)
        result = EvalResult(eval_type=EvalType.BIAS, score=score, passed=score >= 0.7)
        result.details["bias_rate"] = bias_rate
        result.details["bias_words_found"] = bias_count
        self._results.append(result); return result
    def get_results(self) -> List[EvalResult]:
        return list(self._results)
