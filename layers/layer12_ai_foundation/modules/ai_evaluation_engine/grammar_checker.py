"""GrammarChecker — basic grammar and readability check."""
from __future__ import annotations
import re
from typing import List
from .models import EvalResult, EvalType

class GrammarChecker:
    def __init__(self) -> None:
        self._results: List[EvalResult] = []
    def check(self, content: str) -> EvalResult:
        issues: List[str] = []
        if re.search(r"\s{2,}", content): issues.append("Multiple consecutive spaces")
        sentences = re.split(r'[.!?]+', content)
        short_sentences = [s.strip() for s in sentences if s.strip() and len(s.strip().split()) < 3]
        if len(short_sentences) > len(sentences) * 0.5: issues.append("Too many short sentences")
        score = max(0.0, 1.0 - len(issues) * 0.2)
        result = EvalResult(eval_type=EvalType.GRAMMAR, score=score, passed=score >= 0.6)
        result.issues = issues; self._results.append(result); return result
    def get_results(self) -> List[EvalResult]:
        return list(self._results)
