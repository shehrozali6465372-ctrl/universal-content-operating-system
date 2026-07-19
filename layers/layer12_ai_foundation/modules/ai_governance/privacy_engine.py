"""PrivacyEngine — enforce privacy and PII protection."""
from __future__ import annotations
import re
from typing import Any, Dict, List
from .models import Violation

class PrivacyEngine:
    PII_PATTERNS = {
        "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        "phone": r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
        "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
        "credit_card": r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",
    }
    def __init__(self) -> None:
        self._violations: List[Violation] = []
    def check(self, content: str) -> Dict[str, Any]:
        issues: List[str] = []
        for pii_type, pattern in self.PII_PATTERNS.items():
            if re.search(pattern, content):
                issues.append(f"PII detected: {pii_type}")
        score = max(0.0, 1.0 - len(issues) * 0.3)
        if issues:
            self._violations.append(Violation(policy_type="privacy", severity="critical",
                                             description=str(issues)))
        return {"passed": len(issues) == 0, "score": score, "issues": issues}
    def get_violations(self) -> List[Violation]:
        return list(self._violations)
