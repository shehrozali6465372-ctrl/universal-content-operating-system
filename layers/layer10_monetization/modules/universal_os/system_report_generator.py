"""SystemReportGenerator — Daily, weekly, monthly, executive system reports."""
from __future__ import annotations
import itertools
import json
import time
from typing import Any, Dict, List

_SR_COUNTER = itertools.count(1)


class SystemReport:
    """A system report."""

    __slots__ = ("report_id", "report_type", "data", "insights",
                 "recommendations", "timestamp")

    def __init__(self, report_type: str = "daily") -> None:
        self.report_id: str = f"srep_{next(_SR_COUNTER)}"
        self.report_type = report_type
        self.data: Dict[str, Any] = {}
        self.insights: List[str] = []
        self.recommendations: List[str] = []
        self.timestamp: float = time.time()

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
            for i in self.insights:
                lines.append(f"- {i}")
        if self.recommendations:
            lines.append("\n## Recommendations")
            for r in self.recommendations:
                lines.append(f"- {r}")
        return "\n".join(lines)


class SystemReportGenerator:
    """Generate daily, weekly, monthly, and executive reports."""

    def __init__(self) -> None:
        self._reports: List[SystemReport] = []

    def generate(self, report_type: str = "daily",
                 data: Dict[str, Any] = None) -> SystemReport:
        report = SystemReport(report_type)
        if data:
            report.data = dict(data)
        self._reports.append(report)
        return report

    def get_recent(self, count: int = 5) -> List[SystemReport]:
        return self._reports[-count:]

    def get_by_type(self, report_type: str) -> List[SystemReport]:
        return [r for r in self._reports if r.report_type == report_type]

    def get_stats(self) -> Dict[str, Any]:
        types: Dict[str, int] = {}
        for r in self._reports:
            types[r.report_type] = types.get(r.report_type, 0) + 1
        return {"total": len(self._reports), "by_type": types}
