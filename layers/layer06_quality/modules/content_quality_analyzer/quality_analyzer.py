"""Content Quality Analyzer — Central orchestrator for quality checks."""
from __future__ import annotations
import time
from typing import Any, Dict, List

from layers.layer06_quality.modules.content_quality_analyzer.grammar_checker import GrammarChecker
from layers.layer06_quality.modules.content_quality_analyzer.readability_analyzer import ReadabilityAnalyzer
from layers.layer06_quality.modules.content_quality_analyzer.clarity_analyzer import ClarityAnalyzer
from layers.layer06_quality.modules.content_quality_analyzer.structure_analyzer import StructureAnalyzer
from layers.layer06_quality.modules.content_quality_analyzer.engagement_scorer import EngagementScorer


class QualityReport:
    """Complete quality report for content."""
    __slots__ = ("text", "grammar_issues", "readability", "clarity",
                 "structure", "engagement", "overall_score", "grade",
                 "pass_recommendation", "issues", "metadata")

    def __init__(self, text: str = "") -> None:
        self.text = text
        self.grammar_issues: List[Any] = []
        self.readability = None
        self.clarity = None
        self.structure = None
        self.engagement = None
        self.overall_score = 0.0
        self.grade = ""
        self.pass_recommendation = ""
        self.issues: List[str] = []
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "word_count": len(self.text.split()),
            "grammar_issues": len(self.grammar_issues),
            "readability": self.readability.to_dict() if self.readability else None,
            "clarity": self.clarity.to_dict() if self.clarity else None,
            "structure": self.structure.to_dict() if self.structure else None,
            "engagement": self.engagement.to_dict() if self.engagement else None,
            "overall_score": round(self.overall_score, 1),
            "grade": self.grade,
            "pass_recommendation": self.pass_recommendation,
            "issues": self.issues,
        }


class ContentQualityAnalyzer:
    """Central orchestrator for content quality analysis.

    Pipeline: Grammar → Readability → Clarity → Structure → Engagement → Score
    """

    GRADES = [(0.9, "A+"), (0.85, "A"), (0.8, "A-"), (0.75, "B+"),
              (0.7, "B"), (0.65, "B-"), (0.6, "C+"), (0.5, "C"), (0.0, "D")]

    def __init__(self) -> None:
        self.grammar = GrammarChecker()
        self.readability = ReadabilityAnalyzer()
        self.clarity = ClarityAnalyzer()
        self.structure = StructureAnalyzer()
        self.engagement = EngagementScorer()
        self._analysis_count = 0

    def analyze(self, text: str, platform: str = "facebook") -> QualityReport:
        """Run full quality analysis on content."""
        start = time.time()
        report = QualityReport(text=text)

        # 1. Grammar
        report.grammar_issues = self.grammar.check(text)

        # 2. Readability
        report.readability = self.readability.analyze(text)

        # 3. Clarity
        report.clarity = self.clarity.analyze(text)

        # 4. Structure
        report.structure = self.structure.analyze(text)

        # 5. Engagement
        report.engagement = self.engagement.score(text)

        # 6. Overall score
        grammar_score = max(0, 1 - len(report.grammar_issues) * 0.1)
        read_score = (report.readability.flesch_score / 100) if report.readability else 0.5
        clarity_score = report.clarity.clarity_score if report.clarity else 0.5
        structure_score = report.structure.structure_score if report.structure else 0.5
        engagement_score = report.engagement.engagement_score if report.engagement else 0.5

        report.overall_score = round(
            grammar_score * 0.2 + read_score * 0.2 + clarity_score * 0.25 +
            structure_score * 0.15 + engagement_score * 0.2, 3
        )

        # Grade
        for threshold, grade in self.GRADES:
            if report.overall_score >= threshold:
                report.grade = grade
                break

        # Pass/fail
        if report.overall_score >= 0.7:
            report.pass_recommendation = "READY TO PUBLISH"
        elif report.overall_score >= 0.5:
            report.pass_recommendation = "NEEDS IMPROVEMENT"
        else:
            report.pass_recommendation = "REVISION REQUIRED"

        # Collect issues
        if report.grammar_issues:
            report.issues.append(f"{len(report.grammar_issues)} grammar issues found")
        if report.readability and report.readability.issues:
            report.issues.extend(report.readability.issues)
        if report.clarity and report.clarity.issues:
            report.issues.extend(report.clarity.issues)

        report.metadata["pipeline_time_ms"] = round((time.time() - start) * 1000, 2)
        report.metadata["platform"] = platform

        self._analysis_count += 1
        return report

    @property
    def analysis_count(self) -> int:
        return self._analysis_count
