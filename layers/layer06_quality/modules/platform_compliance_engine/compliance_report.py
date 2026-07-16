"""Compliance Report — Result models for platform compliance checking."""
from __future__ import annotations
from typing import Any, Dict, List


class RuleViolation:
    """A single rule violation."""

    __slots__ = ("rule_id", "category", "severity", "description",
                 "current_value", "expected_value", "suggestion", "auto_fixable")

    def __init__(
        self,
        rule_id: str = "",
        category: str = "",
        severity: str = "low",
        description: str = "",
        current_value: str = "",
        expected_value: str = "",
        suggestion: str = "",
        auto_fixable: bool = False,
    ) -> None:
        self.rule_id = rule_id
        self.category = category
        self.severity = severity
        self.description = description
        self.current_value = current_value
        self.expected_value = expected_value
        self.suggestion = suggestion
        self.auto_fixable = auto_fixable

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "category": self.category,
            "severity": self.severity,
            "description": self.description,
            "current_value": self.current_value,
            "expected_value": self.expected_value,
            "suggestion": self.suggestion,
            "auto_fixable": self.auto_fixable,
        }


class PlatformComplianceResult:
    """Compliance result for a single platform."""

    __slots__ = (
        "platform", "is_compliant", "compliance_score",
        "violations", "passed_rules", "total_rules",
    )

    def __init__(self, platform: str = "") -> None:
        self.platform = platform
        self.is_compliant = True
        self.compliance_score = 1.0
        self.violations: List[RuleViolation] = []
        self.passed_rules = 0
        self.total_rules = 0

    def add_violation(self, violation: RuleViolation) -> None:
        self.violations.append(violation)
        if violation.severity == "critical":
            self.is_compliant = False
            self.compliance_score *= 0.3
        elif violation.severity == "high":
            self.is_compliant = False
            self.compliance_score *= 0.6
        elif violation.severity == "medium":
            self.compliance_score *= 0.85

    def compute_score(self) -> None:
        if self.total_rules > 0:
            self.passed_rules = self.total_rules - len(self.violations)
            self.compliance_score = max(0.0, self.passed_rules / self.total_rules)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "platform": self.platform,
            "is_compliant": self.is_compliant,
            "compliance_score": round(self.compliance_score, 3),
            "violation_count": len(self.violations),
            "violations": [v.to_dict() for v in self.violations],
            "passed_rules": self.passed_rules,
            "total_rules": self.total_rules,
        }


class ComplianceReport:
    """Complete platform compliance report."""

    __slots__ = (
        "overall_compliant", "overall_score",
        "platform_results", "auto_fixable_count",
        "statistics",
    )

    def __init__(self) -> None:
        self.overall_compliant = True
        self.overall_score = 1.0
        self.platform_results: List[PlatformComplianceResult] = []
        self.auto_fixable_count = 0
        self.statistics: Dict[str, Any] = {}

    def compute_overall(self) -> None:
        if not self.platform_results:
            self.overall_score = 1.0
            self.statistics = {"platforms_checked": 0}
            return

        self.overall_score = round(
            sum(p.compliance_score for p in self.platform_results) / len(self.platform_results), 3
        )
        self.overall_compliant = all(p.is_compliant for p in self.platform_results)
        self.auto_fixable_count = sum(
            sum(1 for v in p.violations if v.auto_fixable)
            for p in self.platform_results
        )

        self.statistics = {
            "platforms_checked": len(self.platform_results),
            "platforms_compliant": sum(1 for p in self.platform_results if p.is_compliant),
            "total_violations": sum(len(p.violations) for p in self.platform_results),
            "auto_fixable": self.auto_fixable_count,
            "overall_score": self.overall_score,
            "overall_compliant": self.overall_compliant,
        }

    def to_dict(self) -> Dict[str, Any]:
        self.compute_overall()
        return {
            "overall_compliant": self.overall_compliant,
            "overall_score": self.overall_score,
            "platform_results": [p.to_dict() for p in self.platform_results],
            "statistics": self.statistics,
        }
