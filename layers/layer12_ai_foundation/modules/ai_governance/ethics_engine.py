"""EthicsEngine — enforce ethical guidelines."""
from __future__ import annotations
from typing import Any, Dict, List
from .models import Violation

class EthicsEngine:
    GUIDELINES = ["no discrimination", "no harm", "transparency", "fairness", "respect"]
    def __init__(self) -> None:
        self._violations: List[Violation] = []
    def check(self, content: str) -> Dict[str, Any]:
        issues: List[str] = []
        content_lower = content.lower()
        harmful = ["discriminate", "harm", "hate", "prejudice", "exploit"]
        for h in harmful:
            if h in content_lower: issues.append(f"Ethical concern: {h}")
        score = max(0.0, 1.0 - len(issues) * 0.25)
        passed = score >= 0.7
        if not passed:
            v = Violation(policy_type="ethics", severity="high",
                         description=f"Ethical issues: {issues}")
            self._violations.append(v)
        return {"passed": passed, "score": score, "issues": issues}
    def get_violations(self) -> List[Violation]:
        return list(self._violations)
