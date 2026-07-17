"""Report Generator — Create structured analytics reports."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional


class ReportSection:
    """A section within a report."""

    __slots__ = ("title", "content", "metrics", "charts", "order")

    def __init__(self, title: str = "", order: int = 0) -> None:
        self.title = title
        self.content: str = ""
        self.metrics: List[Dict[str, Any]] = []
        self.charts: List[Dict[str, Any]] = []
        self.order = order

    def add_metric(self, name: str, value: Any, unit: str = "") -> None:
        self.metrics.append({"name": name, "value": value, "unit": unit})

    def add_chart(self, chart_type: str, title: str, data: List[Dict[str, Any]]) -> None:
        self.charts.append({"type": chart_type, "title": title, "data": data})

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "content": self.content,
            "metrics": self.metrics,
            "chart_count": len(self.charts),
            "order": self.order,
        }


class AnalyticsReport:
    """A complete analytics report."""

    __slots__ = ("report_id", "title", "period_start", "period_end",
                 "generated_at", "sections", "summary", "metadata")

    def __init__(self, title: str = "") -> None:
        self.report_id: str = f"rpt_{int(time.time() * 1000) % 100000}"
        self.title = title
        self.period_start: float = 0.0
        self.period_end: float = time.time()
        self.generated_at: float = time.time()
        self.sections: List[ReportSection] = []
        self.summary: Dict[str, Any] = {}
        self.metadata: Dict[str, Any] = {}

    def add_section(self, section: ReportSection) -> None:
        self.sections.append(section)
        self.sections.sort(key=lambda s: s.order)

    def get_section(self, title: str) -> Optional[ReportSection]:
        for s in self.sections:
            if s.title == title:
                return s
        return None

    def set_summary(self, key: str, value: Any) -> None:
        self.summary[key] = value

    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "title": self.title,
            "generated_at": self.generated_at,
            "section_count": len(self.sections),
            "summary": self.summary,
            "metadata": self.metadata,
        }


class ReportGenerator:
    """Generate analytics reports from collected data."""

    def __init__(self) -> None:
        self._reports: List[AnalyticsReport] = []
        self._generation_count = 0

    def generate_summary_report(
        self,
        title: str,
        metrics: Dict[str, float],
        period_days: int = 7,
    ) -> AnalyticsReport:
        report = AnalyticsReport(title)
        now = time.time()
        report.period_start = now - (period_days * 86400)
        report.period_end = now

        section = ReportSection("Key Metrics", 1)
        for name, value in metrics.items():
            section.add_metric(name, round(value, 2))
        report.add_section(section)

        summary_section = ReportSection("Executive Summary", 0)
        summary_section.content = self._generate_summary_text(metrics)
        report.add_section(summary_section)

        report.set_summary("total_metrics", len(metrics))
        report.set_summary("period_days", period_days)
        self._reports.append(report)
        self._generation_count += 1
        return report

    def generate_comparison_report(
        self,
        title: str,
        current: Dict[str, float],
        previous: Dict[str, float],
    ) -> AnalyticsReport:
        report = AnalyticsReport(title)
        section = ReportSection("Comparison", 1)
        for key in set(list(current.keys()) + list(previous.keys())):
            curr = current.get(key, 0.0)
            prev = previous.get(key, 0.0)
            change = curr - prev
            pct_change = ((change / abs(prev)) * 100) if prev != 0 else 0.0
            section.add_metric(f"{key}_current", round(curr, 2))
            section.add_metric(f"{key}_change", round(change, 2))
            section.add_metric(f"{key}_pct_change", round(pct_change, 2))
        report.add_section(section)
        self._reports.append(report)
        self._generation_count += 1
        return report

    def get_reports(self, limit: int = 10) -> List[AnalyticsReport]:
        return list(self._reports[-limit:])

    def get_report(self, report_id: str) -> Optional[AnalyticsReport]:
        for r in self._reports:
            if r.report_id == report_id:
                return r
        return None

    def _generate_summary_text(self, metrics: Dict[str, float]) -> str:
        if not metrics:
            return "No data available for this period."
        top_metric = max(metrics.items(), key=lambda x: x[1])
        return f"Key highlight: {top_metric[0]} = {round(top_metric[1], 2)}"

    @property
    def report_count(self) -> int:
        return len(self._reports)
