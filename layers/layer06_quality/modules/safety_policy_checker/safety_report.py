"""Safety Report — Result models for safety and policy validation."""
from __future__ import annotations
from typing import Any, Dict, List


class SafetyFlag:
    """A single safety flag raised during content checking."""

    __slots__ = ("category", "subcategory", "severity", "confidence",
                 "matched_text", "description", "suggestion")

    def __init__(
        self,
        category: str = "",
        subcategory: str = "",
        severity: str = "low",
        confidence: float = 0.0,
        matched_text: str = "",
        description: str = "",
        suggestion: str = "",
    ) -> None:
        self.category = category
        self.subcategory = subcategory
        self.severity = severity
        self.confidence = max(0.0, min(1.0, confidence))
        self.matched_text = matched_text
        self.description = description
        self.suggestion = suggestion

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category,
            "subcategory": self.subcategory,
            "severity": self.severity,
            "confidence": round(self.confidence, 3),
            "matched_text": self.matched_text[:200],
            "description": self.description,
            "suggestion": self.suggestion,
        }


class PolicyCheckResult:
    """Result of checking content against a single platform policy."""

    __slots__ = ("platform", "is_compliant", "flags", "score", "issues")

    def __init__(
        self,
        platform: str = "",
        is_compliant: bool = True,
        score: float = 1.0,
    ) -> None:
        self.platform = platform
        self.is_compliant = is_compliant
        self.flags: List[SafetyFlag] = []
        self.score = max(0.0, min(1.0, score))
        self.issues: List[str] = []

    def add_flag(self, flag: SafetyFlag) -> None:
        self.flags.append(flag)
        if flag.severity == "critical":
            self.is_compliant = False
            self.score *= 0.3
        elif flag.severity == "high":
            self.is_compliant = False
            self.score *= 0.5
        elif flag.severity == "medium":
            self.score *= 0.8

    def to_dict(self) -> Dict[str, Any]:
        return {
            "platform": self.platform,
            "is_compliant": self.is_compliant,
            "score": round(self.score, 3),
            "flag_count": len(self.flags),
            "flags": [f.to_dict() for f in self.flags],
            "issues": self.issues,
        }


class CopyrightResult:
    """Result of copyright/originality checking."""

    __slots__ = ("is_original", "similarity_score", "matched_sources",
                 "flags", "issues")

    def __init__(self) -> None:
        self.is_original = True
        self.similarity_score = 0.0
        self.matched_sources: List[str] = []
        self.flags: List[SafetyFlag] = []
        self.issues: List[str] = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_original": self.is_original,
            "similarity_score": round(self.similarity_score, 3),
            "matched_sources": self.matched_sources,
            "flags": [f.to_dict() for f in self.flags],
            "issues": self.issues,
        }


class SafetyReport:
    """Complete safety and policy report for content."""

    __slots__ = (
        "overall_safe", "overall_score", "harmful_content_flags",
        "spam_flags", "policy_results", "copyright_result",
        "flags", "statistics",
    )

    def __init__(self) -> None:
        self.overall_safe = True
        self.overall_score = 1.0
        self.harmful_content_flags: List[SafetyFlag] = []
        self.spam_flags: List[SafetyFlag] = []
        self.policy_results: List[PolicyCheckResult] = []
        self.copyright_result: CopyrightResult = CopyrightResult()
        self.flags: List[SafetyFlag] = []
        self.statistics: Dict[str, Any] = {}

    def add_flag(self, flag: SafetyFlag) -> None:
        self.flags.append(flag)

    def compute_overall(self) -> None:
        """Compute overall safety from all checks."""
        critical = sum(1 for f in self.flags if f.severity == "critical")
        high = sum(1 for f in self.flags if f.severity == "high")
        medium = sum(1 for f in self.flags if f.severity == "medium")
        low = sum(1 for f in self.flags if f.severity == "low")

        self.overall_score = max(0.0, 1.0 - (critical * 0.3 + high * 0.15 + medium * 0.05 + low * 0.01))

        if critical > 0:
            self.overall_safe = False
        elif high > 2:
            self.overall_safe = False
        elif high > 0:
            self.overall_score = min(self.overall_score, 0.7)
        else:
            self.overall_safe = True

        # Check policy compliance
        for pr in self.policy_results:
            if not pr.is_compliant:
                self.overall_safe = False
                self.overall_score *= 0.5

        self.statistics = {
            "total_flags": len(self.flags),
            "critical_flags": critical,
            "high_flags": high,
            "medium_flags": medium,
            "low_flags": low,
            "policy_platforms_checked": len(self.policy_results),
            "policies_compliant": sum(1 for p in self.policy_results if p.is_compliant),
            "overall_safe": self.overall_safe,
            "overall_score": round(self.overall_score, 3),
        }

    def to_dict(self) -> Dict[str, Any]:
        self.compute_overall()
        return {
            "overall_safe": self.overall_safe,
            "overall_score": self.overall_score,
            "harmful_content_flags": [f.to_dict() for f in self.harmful_content_flags],
            "spam_flags": [f.to_dict() for f in self.spam_flags],
            "policy_results": [p.to_dict() for p in self.policy_results],
            "copyright_result": self.copyright_result.to_dict(),
            "flags": [f.to_dict() for f in self.flags],
            "statistics": self.statistics,
        }
