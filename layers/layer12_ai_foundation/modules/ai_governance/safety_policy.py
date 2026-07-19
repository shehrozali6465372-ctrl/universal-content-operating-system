"""SafetyPolicy — enforce content safety rules."""
from __future__ import annotations
from typing import Any, Dict, List
from .models import Violation

class SafetyPolicy:
    DANGEROUS = ["violence", "self-harm", "illegal", "drugs", "weapons"]
    def __init__(self) -> None:
        self._violations: List[Violation] = []
    def check(self, content: str) -> Dict[str, Any]:
        content_lower = content.lower()
        violations_found = [d for d in self.DANGEROUS if d in content_lower]
        score = max(0.0, 1.0 - len(violations_found) * 0.2)
        if violations_found:
            self._violations.append(Violation(policy_type="safety", severity="critical",
                                             description=str(violations_found)))
        return {"passed": len(violations_found) == 0, "score": score, "issues": violations_found}
    def get_violations(self) -> List[Violation]:
        return list(self._violations)
