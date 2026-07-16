"""Risk Analyzer — Assess overall risk level from quality checks."""
from __future__ import annotations
from typing import List, Optional

from layers.layer06_quality.modules.quality_scoring_engine.quality_result import ModuleScore


class RiskLevel:
    """Risk assessment result."""

    __slots__ = ("level", "score", "factors", "description")

    def __init__(self, level: str = "low", score: float = 0.0) -> None:
        self.level = level
        self.score = max(0.0, min(1.0, score))
        self.factors: List[str] = []
        self.description = ""

    def to_dict(self) -> dict:
        return {
            "level": self.level,
            "score": round(self.score, 3),
            "factors": self.factors,
            "description": self.description,
        }


class RiskAnalyzer:
    """Analyze overall risk from module scores and issues."""

    def __init__(self) -> None:
        self._analyze_count = 0

    def analyze(
        self,
        module_scores: List[ModuleScore],
        overall_score: float = 0.0,
    ) -> RiskLevel:
        """Analyze risk from all module data."""
        risk_score = 0.0
        factors: List[str] = []

        # Safety risk
        safety = self._get_score(module_scores, "safety")
        if safety is not None and safety.score < 50:
            risk_score += 0.3
            factors.append(f"Safety score critically low ({safety.score})")
        elif safety is not None and safety.score < 80:
            risk_score += 0.1
            factors.append(f"Safety score below optimal ({safety.score})")

        # Critical safety issues
        if safety:
            for issue in safety.critical_issues:
                risk_score += 0.15
                factors.append(f"Critical safety: {issue}")

        # Fact validation risk
        facts = self._get_score(module_scores, "fact_validation")
        if facts and facts.score < 50:
            risk_score += 0.2
            factors.append(f"Fact validation critically low ({facts.score})")

        # Compliance risk
        compliance = self._get_score(module_scores, "platform_compliance")
        if compliance and compliance.score < 60:
            risk_score += 0.15
            factors.append(f"Platform compliance issues ({compliance.score})")

        # Overall score risk
        if overall_score < 40:
            risk_score += 0.2
            factors.append(f"Overall quality critically low ({overall_score})")
        elif overall_score < 60:
            risk_score += 0.1
            factors.append(f"Overall quality below threshold ({overall_score})")

        # Low confidence risk
        low_conf = [ms for ms in module_scores if ms.confidence < 0.5]
        if low_conf:
            risk_score += 0.1 * len(low_conf)
            factors.append(f"{len(low_conf)} module(s) with low confidence")

        risk_score = min(1.0, risk_score)

        # Determine level
        if risk_score >= 0.7:
            level = "critical"
            desc = "Critical risk — immediate attention required"
        elif risk_score >= 0.4:
            level = "high"
            desc = "High risk — significant quality concerns"
        elif risk_score >= 0.2:
            level = "medium"
            desc = "Medium risk — some quality concerns to address"
        else:
            level = "low"
            desc = "Low risk — content meets quality standards"

        self._analyze_count += 1
        result = RiskLevel(level=level, score=risk_score)
        result.factors = factors
        result.description = desc
        return result

    def _get_score(self, scores: List[ModuleScore], name: str) -> Optional[ModuleScore]:
        for ms in scores:
            if ms.module_name == name:
                return ms
        return None

    @property
    def analyze_count(self) -> int:
        return self._analyze_count
