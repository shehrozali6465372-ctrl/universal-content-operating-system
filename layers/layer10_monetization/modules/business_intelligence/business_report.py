"""BusinessReport — Generate business intelligence reports."""
from __future__ import annotations
import itertools
import json
import time
from typing import Any, Dict, List

_BR_COUNTER = itertools.count(1)

REPORT_TYPES = ("daily", "weekly", "monthly", "quarterly", "annual", "executive_summary", "revenue_dashboard")


class BusinessReport:
    """A business intelligence report."""

    __slots__ = ("report_id", "report_type", "data", "insights",
                 "recommendations", "score", "timestamp")

    def __init__(self, report_type: str = "daily") -> None:
        self.report_id: str = f"brep_{next(_BR_COUNTER)}"
        self.report_type = report_type if report_type in REPORT_TYPES else "daily"
        self.data: Dict[str, Any] = {}
        self.insights: List[str] = []
        self.recommendations: List[str] = []
        self.score: float = 0.0
        self.timestamp: float = time.time()

    def add_insight(self, insight: str) -> None:
        self.insights.append(insight)

    def add_recommendation(self, rec: str) -> None:
        self.recommendations.append(rec)

    def to_dict(self) -> Dict[str, Any]:
        return {"report_id": self.report_id, "type": self.report_type,
                "data": self.data, "insights": self.insights,
                "recommendations": self.recommendations,
                "score": round(self.score, 2)}

    def export_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    def export_markdown(self) -> str:
        lines = [f"# Business Report: {self.report_type}",
                 f"**Report ID**: {self.report_id}"]
        if self.insights:
            lines.append("\n## Insights")
            for i in self.insights:
                lines.append(f"- {i}")
        if self.recommendations:
            lines.append("\n## Recommendations")
            for r in self.recommendations:
                lines.append(f"- {r}")
        lines.append(f"\n**Score**: {self.score:.2f}")
        return "\n".join(lines)


class BusinessReportGenerator:
    """Generate daily, weekly, monthly, quarterly, and annual business reports."""

    def __init__(self) -> None:
        self._reports: List[BusinessReport] = []

    def generate(self, report_type: str = "daily",
                 data: Dict[str, Any] = None) -> BusinessReport:
        report = BusinessReport(report_type)
        if data:
            report.data = dict(data)
        self._reports.append(report)
        return report

    def generate_insight(self, report_type: str, insight: str) -> BusinessReport:
        report = self.generate(report_type)
        report.add_insight(insight)
        return report

    def generate_recommendation(self, report_type: str,
                                 recommendation: str) -> BusinessReport:
        report = self.generate(report_type)
        report.add_recommendation(recommendation)
        return report

    def get_recent(self, count: int = 5) -> List[BusinessReport]:
        return self._reports[-count:]

    def get_by_type(self, report_type: str) -> List[BusinessReport]:
        return [r for r in self._reports if r.report_type == report_type]

    def get_revenue_dashboard(self, revenue_tracker_data: Dict[str, Any]) -> BusinessReport:
        report = self.generate("revenue_dashboard", revenue_tracker_data)
        total = revenue_tracker_data.get("total_revenue", 0.0)
        report.add_insight(f"Total revenue: ${total:,.2f}")
        return report

    def get_stats(self) -> Dict[str, Any]:
        types: Dict[str, int] = {}
        for r in self._reports:
            types[r.report_type] = types.get(r.report_type, 0) + 1
        return {"total": len(self._reports), "by_type": types}
