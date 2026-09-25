"""SystemReportGenerator — bounded operational report history."""
from __future__ import annotations
import itertools
import json
import time
from typing import Any, Dict, List

_SR_COUNTER = itertools.count(1)


class SystemReport:
    def __init__(self, report_type: str = "daily") -> None:
        self.report_id = f"srep_{next(_SR_COUNTER)}"
        self.report_type = report_type
        self.data: Dict[str, Any] = {}
        self.insights: List[str] = []
        self.recommendations: List[str] = []
        self.timestamp = time.time()

    def add_insight(self, insight: str) -> None:
        self.insights.append(insight)

    def add_recommendation(self, rec: str) -> None:
        self.recommendations.append(rec)

    def to_dict(self) -> Dict[str, Any]:
        return {"report_id": self.report_id, "type": self.report_type,
                "data": self.data, "insights": self.insights,
                "recommendations": self.recommendations}

    def export_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    def export_markdown(self) -> str:
        lines = [f"# System Report: {self.report_type}", f"**ID**: {self.report_id}"]
        if self.insights:
            lines.append("\n## Insights")
            lines.extend(f"- {insight}" for insight in self.insights)
        if self.recommendations:
            lines.append("\n## Recommendations")
            lines.extend(f"- {recommendation}" for recommendation in self.recommendations)
        return "\n".join(lines)


class SystemReportGenerator:
    def __init__(self, max_reports: int = 1000) -> None:
        if max_reports <= 0:
            raise ValueError("max_reports must be positive")
        self._max_reports = max_reports
        self._reports: List[SystemReport] = []

    def generate(self, report_type: str = "daily",
                 data: Dict[str, Any] = None) -> SystemReport:
        report = SystemReport(report_type)
        report.data = dict(data or {})
        self._reports.append(report)
        if len(self._reports) > self._max_reports:
            del self._reports[:-self._max_reports]
        return report

    def get_recent(self, count: int = 5) -> List[SystemReport]:
        return list(self._reports[-max(0, count):])

    def get_by_type(self, report_type: str) -> List[SystemReport]:
        return [report for report in self._reports if report.report_type == report_type]

    def get_stats(self) -> Dict[str, Any]:
        types: Dict[str, int] = {}
        for report in self._reports:
            types[report.report_type] = types.get(report.report_type, 0) + 1
        return {"total": len(self._reports), "by_type": types}
