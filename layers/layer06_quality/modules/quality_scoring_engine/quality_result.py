"""Quality Result — Unified result model for the quality scoring pipeline."""
from __future__ import annotations
from typing import Any, Dict, List, Optional


DECISIONS = ("approve", "approve_with_warnings", "human_review", "revise", "reject")
RISK_LEVELS = ("low", "medium", "high", "critical")
GRADES = ("A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D", "F")


class ModuleScore:
    """Score from a single quality module."""

    __slots__ = ("module_name", "score", "confidence", "weight",
                 "issues", "critical_issues")

    def __init__(
        self,
        module_name: str = "",
        score: float = 0.0,
        confidence: float = 1.0,
        weight: float = 0.0,
    ) -> None:
        self.module_name = module_name
        self.score = max(0.0, min(100.0, score))
        self.confidence = max(0.0, min(1.0, confidence))
        self.weight = weight
        self.issues: List[str] = []
        self.critical_issues: List[str] = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "module_name": self.module_name,
            "score": round(self.score, 1),
            "confidence": round(self.confidence, 3),
            "weight": round(self.weight, 3),
            "issues": self.issues,
            "critical_issues": self.critical_issues,
        }


class ExplanationItem:
    """A single explanation for the decision."""

    __slots__ = ("icon", "text", "category", "severity")

    def __init__(self, icon: str = "", text: str = "", category: str = "", severity: str = "info") -> None:
        self.icon = icon
        self.text = text
        self.category = category
        self.severity = severity

    def to_dict(self) -> Dict[str, Any]:
        return {"icon": self.icon, "text": self.text, "category": self.category, "severity": self.severity}


class QualityResult:
    """Unified quality result for content."""

    __slots__ = (
        "overall_score", "confidence", "grade", "decision",
        "risk_level", "module_scores", "explanations",
        "hard_stops", "statistics",
    )

    def __init__(self) -> None:
        self.overall_score = 0.0
        self.confidence = 0.0
        self.grade = "F"
        self.decision = "reject"
        self.risk_level = "critical"
        self.module_scores: List[ModuleScore] = []
        self.explanations: List[ExplanationItem] = []
        self.hard_stops: List[str] = []
        self.statistics: Dict[str, Any] = {}

    def get_module_score(self, name: str) -> Optional[ModuleScore]:
        for ms in self.module_scores:
            if ms.module_name == name:
                return ms
        return None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_score": round(self.overall_score, 1),
            "confidence": round(self.confidence, 3),
            "grade": self.grade,
            "decision": self.decision,
            "risk_level": self.risk_level,
            "module_scores": {ms.module_name: ms.to_dict() for ms in self.module_scores},
            "explanations": [e.to_dict() for e in self.explanations],
            "hard_stops": self.hard_stops,
            "statistics": self.statistics,
        }
