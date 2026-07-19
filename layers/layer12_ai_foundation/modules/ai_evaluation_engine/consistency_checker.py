"""ConsistencyChecker — check content consistency."""
from __future__ import annotations
from typing import Any, Dict, List
from .models import EvalResult, EvalType

class ConsistencyChecker:
    def __init__(self) -> None:
        self._results: List[EvalResult] = []
    def check(self, content: str, context: Dict[str, Any] | None = None) -> EvalResult:
        issues: List[str] = []
        paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
        if len(paragraphs) > 1:
            first_words = set()
            for p in paragraphs:
                first_word = p.split()[0].lower() if p.split() else ""
                first_words.add(first_word)
            if len(first_words) < len(paragraphs) * 0.5:
                issues.append("Repetitive paragraph beginnings")
        score = max(0.0, 1.0 - len(issues) * 0.2)
        result = EvalResult(eval_type=EvalType.CONSISTENCY, score=score, passed=score >= 0.6)
        result.issues = issues; self._results.append(result); return result
    def get_results(self) -> List[EvalResult]:
        return list(self._results)
