"""Voice Report — Result models for brand voice consistency checking."""
from __future__ import annotations
from typing import Any, Dict, List


class VoiceIssue:
    """A single brand voice issue."""

    __slots__ = ("category", "severity", "description", "suggestion",
                 "current_value", "expected_value")

    def __init__(
        self,
        category: str = "",
        severity: str = "low",
        description: str = "",
        suggestion: str = "",
        current_value: str = "",
        expected_value: str = "",
    ) -> None:
        self.category = category
        self.severity = severity
        self.description = description
        self.suggestion = suggestion
        self.current_value = current_value
        self.expected_value = expected_value

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category,
            "severity": self.severity,
            "description": self.description,
            "suggestion": self.suggestion,
            "current_value": self.current_value,
            "expected_value": self.expected_value,
        }


class VoiceComponentScore:
    """Score for a single voice component."""

    __slots__ = ("component", "score", "status", "issues")

    def __init__(self, component: str = "", score: float = 0.0) -> None:
        self.component = component
        self.score = max(0.0, min(1.0, score))
        self.status = "unknown"
        self.issues: List[VoiceIssue] = []

    def compute_status(self) -> None:
        if self.score >= 0.85:
            self.status = "excellent"
        elif self.score >= 0.7:
            self.status = "good"
        elif self.score >= 0.5:
            self.status = "fair"
        else:
            self.status = "poor"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "component": self.component,
            "score": round(self.score, 3),
            "status": self.status,
            "issue_count": len(self.issues),
        }


class VoiceReport:
    """Complete brand voice consistency report."""

    __slots__ = (
        "brand_name", "overall_score", "is_consistent",
        "component_scores", "issues", "statistics",
    )

    def __init__(self, brand_name: str = "") -> None:
        self.brand_name = brand_name
        self.overall_score = 0.0
        self.is_consistent = True
        self.component_scores: List[VoiceComponentScore] = []
        self.issues: List[VoiceIssue] = []
        self.statistics: Dict[str, Any] = {}

    def compute_overall(self) -> None:
        if not self.component_scores:
            self.overall_score = 0.5
            return

        total = sum(c.score for c in self.component_scores)
        self.overall_score = round(total / len(self.component_scores), 3)
        self.is_consistent = self.overall_score >= 0.7

        self.statistics = {
            "brand_name": self.brand_name,
            "overall_score": self.overall_score,
            "is_consistent": self.is_consistent,
            "components_checked": len(self.component_scores),
            "components_good": sum(1 for c in self.component_scores if c.status in ("excellent", "good")),
            "total_issues": len(self.issues),
            "critical_issues": sum(1 for i in self.issues if i.severity == "critical"),
            "high_issues": sum(1 for i in self.issues if i.severity == "high"),
        }

    def to_dict(self) -> Dict[str, Any]:
        self.compute_overall()
        return {
            "brand_name": self.brand_name,
            "overall_score": self.overall_score,
            "is_consistent": self.is_consistent,
            "component_scores": [c.to_dict() for c in self.component_scores],
            "issues": [i.to_dict() for i in self.issues],
            "statistics": self.statistics,
        }
