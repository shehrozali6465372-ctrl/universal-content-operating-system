"""SEOChecker — evaluate SEO quality."""
from __future__ import annotations
from typing import List
from .models import EvalResult, EvalType

class SEOChecker:
    def __init__(self) -> None:
        self._results: List[EvalResult] = []
    def check(self, content: str, keywords: list | None = None) -> EvalResult:
        score = 0.5; issues: List[str] = []
        if len(content) > 300: score += 0.15
        elif len(content) < 100: issues.append("Content too short for SEO")
        if keywords:
            content_lower = content.lower()
            found = sum(1 for k in keywords if k.lower() in content_lower)
            score += (found / max(len(keywords), 1)) * 0.2
        if content and content[0].isupper(): score += 0.05
        score = min(1.0, score)
        result = EvalResult(eval_type=EvalType.SEO, score=score, passed=score >= 0.5)
        result.issues = issues; self._results.append(result); return result
    def get_results(self) -> List[EvalResult]:
        return list(self._results)
