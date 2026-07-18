"""ResearchReport — Generate research reports."""
from __future__ import annotations
import itertools
import time
from typing import Any, Dict, List

_RR_COUNTER = itertools.count(1)


class ResearchReport:
    """A research report."""

    __slots__ = ("report_id", "report_type", "data", "recommendations",
                 "timestamp")

    def __init__(self, report_type: str = "daily") -> None:
        self.report_id: str = f"rrpt_{next(_RR_COUNTER)}"
        self.report_type = report_type
        self.data: Dict[str, Any] = {}
        self.recommendations: List[str] = []
        self.timestamp: float = time.time()

    def set_data(self, data: Dict[str, Any]) -> None:
        self.data = dict(data)

    def add_recommendation(self, rec: str) -> None:
        self.recommendations.append(rec)

    def get_summary(self) -> Dict[str, Any]:
        return {"report_id": self.report_id, "report_type": self.report_type,
                "recommendation_count": len(self.recommendations)}

    def export_dict(self) -> Dict[str, Any]:
        return {**self.get_summary(), "data": self.data,
                "recommendations": self.recommendations}


class ResearchReportGenerator:
    """Generate daily, weekly, monthly, platform, competitor, and trend reports."""

    def __init__(self) -> None:
        self._reports: List[ResearchReport] = []

    def generate(self, report_type: str = "daily",
                 data: Dict[str, Any] = None) -> ResearchReport:
        report = ResearchReport(report_type)
        if data:
            report.set_data(data)
        self._reports.append(report)
        return report

    def get_recent(self, count: int = 5) -> List[ResearchReport]:
        return self._reports[-count:]

    def get_stats(self) -> Dict[str, Any]:
        return {"total": len(self._reports)}
