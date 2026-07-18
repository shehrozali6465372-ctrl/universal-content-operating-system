"""AnalyticsReport — Generate analytics intelligence reports."""
from __future__ import annotations
import itertools
import time
from typing import Any, Dict, List

_AR_COUNTER = itertools.count(1)


class AnalyticsReport:
    """An analytics intelligence report."""

    __slots__ = ("report_id", "report_type", "data", "insights",
                 "recommendations", "scores", "timestamp")

    def __init__(self, report_type: str = "daily") -> None:
        self.report_id: str = f"arpt_{next(_AR_COUNTER)}"
        self.report_type = report_type
        self.data: Dict[str, Any] = {}
        self.insights: List[str] = []
        self.recommendations: List[str] = []
        self.scores: Dict[str, float] = {}
        self.timestamp: float = time.time()

    def add_insight(self, insight: str) -> None:
        self.insights.append(insight)

    def add_recommendation(self, rec: str) -> None:
        self.recommendations.append(rec)

    def set_score(self, metric: str, value: float) -> None:
        self.scores[metric] = value

    def to_dict(self) -> Dict[str, Any]:
        return {"report_id": self.report_id, "report_type": self.report_type,
                "data": self.data, "insights": self.insights,
                "recommendations": self.recommendations,
                "scores": self.scores}

    def get_summary(self) -> Dict[str, Any]:
        return {"report_id": self.report_id, "report_type": self.report_type,
                "insight_count": len(self.insights),
                "recommendation_count": len(self.recommendations),
                "score_count": len(self.scores)}


class AnalyticsReportGenerator:
    """Generate comprehensive analytics intelligence reports."""

    def __init__(self) -> None:
        self._reports: List[AnalyticsReport] = []

    def generate(self, report_type: str = "daily",
                 data: Dict[str, Any] = None) -> AnalyticsReport:
        report = AnalyticsReport(report_type)
        if data:
            report.data = dict(data)
        self._reports.append(report)
        return report

    def generate_performance_report(self, scores: Dict[str, float],
                                    insights: List[str] = None) -> AnalyticsReport:
        report = self.generate("performance")
        for metric, value in scores.items():
            report.set_score(metric, value)
        if insights:
            for i in insights:
                report.add_insight(i)
        return report

    def generate_optimization_report(self, recommendations: List[str],
                                     data: Dict[str, Any] = None) -> AnalyticsReport:
        report = self.generate("optimization", data)
        for rec in recommendations:
            report.add_recommendation(rec)
        return report

    def get_recent(self, count: int = 5) -> List[AnalyticsReport]:
        return self._reports[-count:]

    def get_by_type(self, report_type: str) -> List[AnalyticsReport]:
        return [r for r in self._reports if r.report_type == report_type]

    def get_stats(self) -> Dict[str, Any]:
        types: Dict[str, int] = {}
        for r in self._reports:
            types[r.report_type] = types.get(r.report_type, 0) + 1
        return {"total": len(self._reports), "by_type": types}
