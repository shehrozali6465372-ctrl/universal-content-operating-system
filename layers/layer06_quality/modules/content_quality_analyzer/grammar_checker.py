"""Grammar Checker — Detect common grammar issues in content."""
from __future__ import annotations
import re
from typing import Any, Dict, List


COMMON_ERRORS = {
    "your_youre": (r'\byour\s+(?:is|are|was|were|have|has|had|will|would|could|should|can|going|good|amazing|the|best|worst)\b', "Use 'you\'re' (you are)"),
    "its_itis": (r'\bits\s+(?:is|are|was|were|has|had|will|would|could|should|going)\b', "Use 'it\'s' (it is)"),
    "their_there": (r'\btheir\s+(?:is|are|was|were)\b', "Consider 'there' instead of 'their'"),
    "a_an": (r'\ba\s+[aeiou]', "Consider 'an' before vowel sounds"),
    "double_space": (r'  +', "Multiple spaces detected"),
    "trailing_space": (r'\s+$', "Trailing whitespace"),
    "repeated_word": (r'\b(\w+)\s+\1\b', "Repeated word"),
    "missing_period": (r'^[A-Z][^.!?\n]+$', "Sentence may be missing ending punctuation"),
    "start_lowercase": (r'(?<=\.\s)[a-z]', "Sentence should start with capital letter"),
}


class GrammarIssue:
    """A single grammar issue."""
    __slots__ = ("rule", "message", "position", "severity", "suggestion")

    def __init__(self, rule: str = "", message: str = "") -> None:
        self.rule = rule
        self.message = message
        self.position = (0, 0)
        self.severity = "warning"
        self.suggestion = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule": self.rule,
            "message": self.message,
            "severity": self.severity,
            "suggestion": self.suggestion,
        }


class GrammarChecker:
    """Checks content for common grammar issues."""

    def __init__(self) -> None:
        self._check_count = 0

    def check(self, text: str) -> List[GrammarIssue]:
        """Check text for grammar issues."""
        issues: List[GrammarIssue] = []
        for rule_name, (pattern, message) in COMMON_ERRORS.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                issue = GrammarIssue(rule=rule_name, message=message)
                issue.position = (match.start(), match.end())
                if rule_name in ("your_youre", "its_itis", "their_there"):
                    issue.severity = "error"
                issues.append(issue)
        self._check_count += 1
        return issues

    def check_batch(self, texts: List[str]) -> List[List[GrammarIssue]]:
        """Check multiple texts."""
        return [self.check(t) for t in texts]

    @property
    def check_count(self) -> int:
        return self._check_count
