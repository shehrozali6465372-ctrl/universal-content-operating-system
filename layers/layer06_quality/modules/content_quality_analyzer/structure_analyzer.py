"""Structure Analyzer — Analyze content structure and organization."""
from __future__ import annotations
from typing import Any, Dict, List


class StructureResult:
    """Structure analysis result."""
    __slots__ = ("has_hook", "has_body", "has_cta", "has_conclusion",
                 "paragraph_count", "heading_count", "list_detected",
                 "structure_score", "issues", "structure_type")

    def __init__(self) -> None:
        self.has_hook = False
        self.has_body = True
        self.has_cta = False
        self.has_conclusion = False
        self.paragraph_count = 0
        self.heading_count = 0
        self.list_detected = False
        self.structure_score = 0.0
        self.issues: List[str] = []
        self.structure_type = "unknown"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "has_hook": self.has_hook,
            "has_body": self.has_body,
            "has_cta": self.has_cta,
            "has_conclusion": self.has_conclusion,
            "paragraph_count": self.paragraph_count,
            "heading_count": self.heading_count,
            "list_detected": self.list_detected,
            "structure_score": round(self.structure_score, 3),
            "structure_type": self.structure_type,
            "issues": self.issues,
        }


CTA_SIGNALS = {"comment", "share", "follow", "subscribe", "like", "click", "visit", "check", "join", "sign up", "let us know", "tell us", "what do you think"}
HOOK_SIGNALS = {"did you know", "what if", "imagine", "here's", "discover", "uncover", "revealed", "secret"}


class StructureAnalyzer:
    """Analyzes content structure and organization."""

    def __init__(self) -> None:
        self._analysis_count = 0

    def analyze(self, text: str) -> StructureResult:
        """Analyze text structure."""
        result = StructureResult()
        text_lower = text.lower()
        words = text_lower.split()

        # Paragraphs
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        result.paragraph_count = max(len(paragraphs), 1)

        # Headings
        result.heading_count = sum(1 for line in text.split('\n')
                                    if line.strip().startswith(('#', '##', '###')))

        # Lists
        result.list_detected = any(line.strip().startswith(('- ', '* ', '1.', '2.', '3.'))
                                    for line in text.split('\n'))

        # Hook detection
        result.has_hook = any(signal in text_lower for signal in HOOK_SIGNALS) or len(words) > 0

        # CTA detection
        result.has_cta = any(signal in text_lower for signal in CTA_SIGNALS)

        # Conclusion
        conclusion_signals = {"in conclusion", "to summarize", "in summary", "finally", "overall", "in short"}
        result.has_conclusion = any(signal in text_lower for signal in conclusion_signals)

        # Structure type
        if result.heading_count > 0:
            result.structure_type = "article"
        elif result.list_detected:
            result.structure_type = "listicle"
        elif result.paragraph_count <= 2:
            result.structure_type = "short_post"
        else:
            result.structure_type = "long_post"

        # Score
        score = 50.0
        if result.has_hook:
            score += 15
        if result.has_cta:
            score += 15
        if result.has_conclusion:
            score += 10
        if result.paragraph_count >= 2:
            score += 10
        result.structure_score = min(score, 100) / 100

        if not result.has_cta:
            result.issues.append("No CTA found in content")

        self._analysis_count += 1
        return result

    @property
    def analysis_count(self) -> int:
        return self._analysis_count
