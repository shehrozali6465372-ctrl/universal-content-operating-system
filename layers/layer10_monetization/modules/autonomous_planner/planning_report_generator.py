"""PlanningReportGenerator — Generate planning reports."""
from __future__ import annotations
import itertools
import time
from typing import Any, Dict, List, Optional

_PRG_COUNTER = itertools.count(1)


class PlanningReport:
    """A planning report."""

    __slots__ = ("report_id", "report_type", "planning_summary", "risk_summary",
                 "resource_summary", "opportunity_summary", "recommendations",
                 "timestamp")

    def __init__(self, report_type: str = "planning") -> None:
        self.report_id: str = f"prep_{next(_PRG_COUNTER)}"
        self.report_type = report_type
        self.planning_summary: Dict[str, Any] = {}
        self.risk_summary: Dict[str, Any] = {}
        self.resource_summary: Dict[str, Any] = {}
        self.opportunity_summary: Dict[str, Any] = {}
        self.recommendations: List[str] = []
        self.timestamp: float = time.time()

    def set_planning_summary(self, data: Dict[str, Any]) -> None:
        self.planning_summary = dict(data)

    def set_risk_summary(self, data: Dict[str, Any]) -> None:
        self.risk_summary = dict(data)

    def set_resource_summary(self, data: Dict[str, Any]) -> None:
        self.resource_summary = dict(data)

    def set_opportunity_summary(self, data: Dict[str, Any]) -> None:
        self.opportunity_summary = dict(data)

    def add_recommendation(self, rec: str) -> None:
        self.recommendations.append(rec)

    def get_summary(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id, "report_type": self.report_type,
            "recommendation_count": len(self.recommendations),
        }

    def export_dict(self) -> Dict[str, Any]:
        return {
            **self.get_summary(),
            "planning": self.planning_summary, "risks": self.risk_summary,
            "resources": self.resource_summary, "opportunities": self.opportunity_summary,
            "recommendations": self.recommendations,
        }


class PlanningReportGenerator:
    """Generate planning, risk, resource, and opportunity reports."""

    def __init__(self) -> None:
        self._reports: List[PlanningReport] = []

    def generate(self, report_type: str = "planning",
                 data: Optional[Dict[str, Any]] = None) -> PlanningReport:
        report = PlanningReport(report_type)
        if data:
            report.set_planning_summary(data)
        self._reports.append(report)
        return report

    def get_report(self, report_id: str) -> PlanningReport:
        for r in self._reports:
            if r.report_id == report_id:
                return r
        return None

    def get_recent(self, count: int = 5) -> List[PlanningReport]:
        return self._reports[-count:]

    def get_stats(self) -> Dict[str, Any]:
        return {"total_reports": len(self._reports)}
