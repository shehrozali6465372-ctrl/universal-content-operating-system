"""CopyrightChecker — detect copyright infringements."""
from __future__ import annotations
from typing import Any, Dict, List
from .models import Violation

class CopyrightChecker:
    def __init__(self) -> None:
        self._violations: List[Violation] = []
    def check(self, content: str, source_text: str = "") -> Dict[str, Any]:
        issues: List[str] = []
        if source_text:
            content_words = set(content.lower().split())
            source_words = set(source_text.lower().split())
            overlap = len(content_words & source_words) / max(len(source_words), 1)
            if overlap > 0.7: issues.append(f"High text similarity: {overlap:.1%}")
        if "copyright" in content.lower() and "©" in content:
            issues.append("May contain copyrighted notice")
        score = max(0.0, 1.0 - len(issues) * 0.4)
        if issues:
            self._violations.append(Violation(policy_type="copyright", severity="high",
                                             description=str(issues)))
        return {"passed": len(issues) == 0, "score": score, "issues": issues}
    def get_violations(self) -> List[Violation]:
        return list(self._violations)
