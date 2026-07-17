"""Meta Report Generator — Generate system reports."""
from __future__ import annotations
import itertools
import time
from typing import Any, Dict, List, Optional

_MRG_COUNTER = itertools.count(1)


class MetaReport:
    """A system-wide report."""

    __slots__ = ("report_id", "report_type", "period", "data",
                 "recommendations", "timestamp")

    def __init__(self, report_type: str = "daily") -> None:
        self.report_id: str = f"mrep_{next(_MRG_COUNTER)}"
        self.report_type = report_type
        self.period: str = ""
        self.data: Dict[str, Any] = {}
        self.recommendations: List[str] = []
        self.timestamp: float = time.time()

    def set_data(self, data: Dict[str, Any]) -> None:
        self.data = dict(data)

    def add_recommendation(self, rec: str) -> None:
        self.recommendations.append(rec)

    def get_summary(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id, "report_type": self.report_type,
            "data_keys": list(self.data.keys()),
            "recommendation_count": len(self.recommendations),
        }

    def export_dict(self) -> Dict[str, Any]:
        return {**self.get_summary(), "data": self.data, "recommendations": self.recommendations}


class MetaReportGenerator:
    """Generate daily, weekly, monthly, campaign, and platform reports."""

    def __init__(self) -> None:
        self._reports: List[MetaReport] = []

    def generate(self, report_type: str = "daily",
                 data: Optional[Dict[str, Any]] = None) -> MetaReport:
        report = MetaReport(report_type)
        if data:
            report.set_data(data)
        self._reports.append(report)
        return report

    def get_report(self, report_id: str) -> MetaReport:
        for r in self._reports:
            if r.report_id == report_id:
                return r
        return None

    def get_recent(self, count: int = 5) -> List[MetaReport]:
        return self._reports[-count:]

    def get_stats(self) -> Dict[str, Any]:
        types: Dict[str, int] = {}
        for r in self._reports:
            types[r.report_type] = types.get(r.report_type, 0) + 1
        return {"total": len(self._reports), "by_type": types}
