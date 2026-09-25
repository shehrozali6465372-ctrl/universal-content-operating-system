"""Structured analytics reports with collision-safe identifiers."""
from __future__ import annotations
import time
import uuid
from threading import RLock
from typing import Any, Dict, List, Optional


class ReportSection:
    __slots__ = ("title", "content", "metrics", "charts", "order")
    def __init__(self, title: str = "", order: int = 0) -> None:
        self.title, self.order, self.content = title, order, ""
        self.metrics: List[Dict[str, Any]] = []; self.charts: List[Dict[str, Any]] = []
    def add_metric(self, name: str, value: Any, unit: str = "") -> None:
        self.metrics.append({"name": name, "value": value, "unit": unit})
    def add_chart(self, chart_type: str, title: str, data: List[Dict[str, Any]]) -> None:
        self.charts.append({"type": chart_type, "title": title, "data": list(data)})
    def to_dict(self) -> Dict[str, Any]:
        return {"title": self.title, "content": self.content, "metrics": list(self.metrics),
                "chart_count": len(self.charts), "order": self.order}


class AnalyticsReport:
    __slots__ = ("report_id", "title", "period_start", "period_end", "generated_at", "sections", "summary", "metadata")
    def __init__(self, title: str = "") -> None:
        self.report_id, self.title = f"rpt_{uuid.uuid4().hex}", title
        self.period_start = 0.0; self.period_end = time.time(); self.generated_at = time.time()
        self.sections: List[ReportSection] = []; self.summary: Dict[str, Any] = {}; self.metadata: Dict[str, Any] = {}
    def add_section(self, section: ReportSection) -> None:
        self.sections.append(section); self.sections.sort(key=lambda s: s.order)
    def get_section(self, title: str) -> Optional[ReportSection]:
        return next((s for s in self.sections if s.title == title), None)
    def set_summary(self, key: str, value: Any) -> None: self.summary[key] = value
    def to_dict(self) -> Dict[str, Any]:
        return {"report_id": self.report_id, "title": self.title, "generated_at": self.generated_at,
                "section_count": len(self.sections), "summary": dict(self.summary), "metadata": dict(self.metadata)}


class ReportGenerator:
    def __init__(self) -> None:
        self._reports: List[AnalyticsReport] = []; self._generation_count = 0; self._lock = RLock()
    def generate_summary_report(self, title: str, metrics: Dict[str, float], period_days: int = 7) -> AnalyticsReport:
        if period_days <= 0: raise ValueError("period_days must be positive")
        if any(not isinstance(v, (int, float)) for v in metrics.values()): raise ValueError("metrics must be numeric")
        report = AnalyticsReport(title); now = time.time()
        report.period_start, report.period_end = now - period_days * 86400, now
        summary = ReportSection("Executive Summary", 0); summary.content = self._generate_summary_text(metrics)
        report.add_section(summary)
        section = ReportSection("Key Metrics", 1)
        for name, value in metrics.items(): section.add_metric(name, round(float(value), 2))
        report.add_section(section); report.set_summary("total_metrics", len(metrics)); report.set_summary("period_days", period_days)
        with self._lock: self._reports.append(report); self._generation_count += 1
        return report
    def generate_comparison_report(self, title: str, current: Dict[str, float], previous: Dict[str, float]) -> AnalyticsReport:
        report = AnalyticsReport(title); section = ReportSection("Comparison", 1)
        for key in sorted(set(current) | set(previous)):
            curr, prev = float(current.get(key, 0.0)), float(previous.get(key, 0.0))
            change = curr - prev; pct = change / abs(prev) * 100 if prev else 0.0
            section.add_metric(f"{key}_current", round(curr, 2)); section.add_metric(f"{key}_change", round(change, 2)); section.add_metric(f"{key}_pct_change", round(pct, 2))
        report.add_section(section)
        with self._lock: self._reports.append(report); self._generation_count += 1
        return report
    def get_reports(self, limit: int = 10) -> List[AnalyticsReport]:
        if limit < 0: raise ValueError("limit must be non-negative")
        with self._lock: return list(self._reports[-limit:]) if limit else []
    def get_report(self, report_id: str) -> Optional[AnalyticsReport]:
        with self._lock: return next((r for r in self._reports if r.report_id == report_id), None)
    @staticmethod
    def _generate_summary_text(metrics: Dict[str, float]) -> str:
        if not metrics: return "No data available for this period."
        key, value = max(metrics.items(), key=lambda x: abs(x[1]))
        return f"Key highlight: {key} = {round(value, 2)}"
    @property
    def report_count(self) -> int:
        with self._lock: return len(self._reports)
