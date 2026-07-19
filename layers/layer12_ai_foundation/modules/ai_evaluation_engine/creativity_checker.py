"""CreativityChecker — evaluate content creativity."""
from __future__ import annotations
from typing import List
from .models import EvalResult, EvalType

class CreativityChecker:
    def __init__(self) -> None:
        self._results: List[EvalResult] = []
    def check(self, content: str) -> EvalResult:
        words = content.split()
        unique_words = set(w.lower() for w in words)
        vocab_richness = len(unique_words) / max(len(words), 1)
        avg_word_len = sum(len(w) for w in words) / max(len(words), 1)
        score = min(1.0, vocab_richness * 0.5 + min(avg_word_len / 8, 0.3) + 0.2)
        result = EvalResult(eval_type=EvalType.CREATIVITY, score=score, passed=score >= 0.4)
        result.details["vocab_richness"] = round(vocab_richness, 4)
        self._results.append(result); return result
    def get_results(self) -> List[EvalResult]:
        return list(self._results)
