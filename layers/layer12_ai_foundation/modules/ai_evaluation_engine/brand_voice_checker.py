"""BrandVoiceChecker — evaluate brand voice compliance."""
from __future__ import annotations
from typing import Dict, List
from .models import EvalResult, EvalType

class BrandVoiceChecker:
    def __init__(self, brand_tone: str = "professional") -> None:
        self.brand_tone = brand_tone; self._results: List[EvalResult] = []
    def check(self, content: str, brand_guidelines: Dict[str, str] | None = None) -> EvalResult:
        issues: List[str] = []
        if brand_guidelines:
            forbidden = brand_guidelines.get("forbidden_words", [])
            content_lower = content.lower()
            found = [w for w in forbidden if w.lower() in content_lower]
            if found: issues.append(f"Forbidden words: {found}")
        score = max(0.0, 1.0 - len(issues) * 0.3)
        result = EvalResult(eval_type=EvalType.BRAND_VOICE, score=score, passed=score >= 0.5)
        result.issues = issues; self._results.append(result); return result
    def get_results(self) -> List[EvalResult]:
        return list(self._results)
