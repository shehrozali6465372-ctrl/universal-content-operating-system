"""Prompt Analyzer — Analyze what makes prompts work or fail."""
from __future__ import annotations
from typing import Any, Dict, List

from layers.layer09_learning.modules.prompt_optimization.prompt_profile import PromptProfile


class AnalysisFinding:
    """A single analysis finding about a prompt."""

    __slots__ = ("finding_id", "category", "severity", "description",
                 "metric_name", "metric_value", "recommendation")

    _counter = 0

    def __init__(self, category: str = "", severity: str = "info") -> None:
        PromptAnalyzer._counter += 1
        self.finding_id: str = f"af_{PromptAnalyzer._counter}"
        self.category = category
        self.severity = severity
        self.description: str = ""
        self.metric_name: str = ""
        self.metric_value: float = 0.0
        self.recommendation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "finding_id": self.finding_id,
            "category": self.category,
            "severity": self.severity,
            "description": self.description,
            "metric_name": self.metric_name,
            "recommendation": self.recommendation,
        }


class AnalysisReport:
    """Complete analysis report for a prompt."""

    __slots__ = ("profile_id", "findings", "overall_health", "score")

    def __init__(self, profile_id: str = "") -> None:
        self.profile_id = profile_id
        self.findings: List[AnalysisFinding] = []
        self.overall_health: str = "unknown"
        self.score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "finding_count": len(self.findings),
            "overall_health": self.overall_health,
            "score": round(self.score, 3),
        }


class PromptAnalyzer:
    """Analyze prompt effectiveness and identify improvement areas."""

    _counter = 0

    HEALTH_THRESHOLDS = {"excellent": 85.0, "good": 70.0, "fair": 50.0}

    def __init__(self) -> None:
        self._reports: List[AnalysisReport] = []

    def analyze(self, profile: PromptProfile) -> AnalysisReport:
        report = AnalysisReport(profile.profile_id)
        findings = []
        findings.extend(self._analyze_engagement(profile))
        findings.extend(self._analyze_quality(profile))
        findings.extend(self._analyze_usage(profile))
        findings.extend(self._analyze_template(profile))
        report.findings = findings
        report.score = self._compute_health_score(findings, profile)
        report.overall_health = self._classify_health(report.score)
        self._reports.append(report)
        return report

    def _analyze_engagement(self, p: PromptProfile) -> List[AnalysisFinding]:
        findings = []
        if p.usage_count > 0 and p.avg_engagement < 0.3:
            f = AnalysisFinding("engagement", "warning")
            f.description = f"Low average engagement: {p.avg_engagement}"
            f.metric_name = "avg_engagement"
            f.metric_value = p.avg_engagement
            f.recommendation = "Consider revising tone or hook in the prompt"
            findings.append(f)
        if p.success_rate > 0 and p.success_rate < 0.5:
            f = AnalysisFinding("engagement", "critical")
            f.description = f"Low success rate: {p.success_rate}"
            f.metric_name = "success_rate"
            f.metric_value = p.success_rate
            f.recommendation = "Major prompt revision needed"
            findings.append(f)
        return findings

    def _analyze_quality(self, p: PromptProfile) -> List[AnalysisFinding]:
        findings = []
        if p.usage_count > 0 and p.avg_quality_score < 0.5:
            f = AnalysisFinding("quality", "warning")
            f.description = f"Below average quality: {p.avg_quality_score}"
            f.metric_name = "avg_quality_score"
            f.metric_value = p.avg_quality_score
            f.recommendation = "Add more specific instructions to the prompt"
            findings.append(f)
        return findings

    def _analyze_usage(self, p: PromptProfile) -> List[AnalysisFinding]:
        findings = []
        if p.usage_count == 0:
            f = AnalysisFinding("usage", "info")
            f.description = "Prompt has never been used"
            f.metric_name = "usage_count"
            f.metric_value = 0.0
            f.recommendation = "Test this prompt to gather performance data"
            findings.append(f)
        elif p.usage_count < 5:
            f = AnalysisFinding("usage", "info")
            f.description = f"Low usage count: {p.usage_count}. Results may not be statistically significant."
            f.metric_name = "usage_count"
            f.metric_value = float(p.usage_count)
            f.recommendation = "Gather more usage data before making optimization decisions"
            findings.append(f)
        return findings

    def _analyze_template(self, p: PromptProfile) -> List[AnalysisFinding]:
        findings = []
        if not p.template:
            f = AnalysisFinding("template", "critical")
            f.description = "Empty prompt template"
            f.recommendation = "Add prompt content"
            findings.append(f)
        elif len(p.template) < 20:
            f = AnalysisFinding("template", "warning")
            f.description = f"Very short template ({len(p.template)} chars)"
            f.recommendation = "Consider adding more detailed instructions"
            findings.append(f)
        return findings

    def _compute_health_score(self, findings: List[AnalysisFinding], profile: PromptProfile) -> float:
        score = 100.0
        for f in findings:
            if f.severity == "critical":
                score -= 25.0
            elif f.severity == "warning":
                score -= 10.0
        if profile.usage_count > 5:
            score += min(10.0, profile.avg_engagement * 10)
        return max(0.0, min(100.0, score))

    def _classify_health(self, score: float) -> str:
        if score >= self.HEALTH_THRESHOLDS["excellent"]:
            return "excellent"
        elif score >= self.HEALTH_THRESHOLDS["good"]:
            return "good"
        elif score >= self.HEALTH_THRESHOLDS["fair"]:
            return "fair"
        return "poor"

    def get_reports(self) -> List[AnalysisReport]:
        return list(self._reports)

    def get_critical_findings(self) -> List[AnalysisFinding]:
        critical = []
        for report in self._reports:
            critical.extend(f for f in report.findings if f.severity == "critical")
        return critical
