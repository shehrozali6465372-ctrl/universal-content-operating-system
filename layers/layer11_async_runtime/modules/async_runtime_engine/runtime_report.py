"""RuntimeReport — Generate runtime performance reports."""
from __future__ import annotations
import json
import time
from typing import Any, Dict, List


class RuntimeReport:
    """A runtime performance report."""
    __slots__ = ("report_id", "report_type", "data", "insights", "recommendations", "timestamp")

    def __init__(self, report_type: str = "status") -> None:
        self.report_id = f"rrpt_{int(time.time())}"
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


class RuntimeReportGenerator:
    """Generate runtime performance reports."""
    def __init__(self) -> None:
        self._reports: List[RuntimeReport] = []

    def generate(self, report_type: str = "status",
                 data: Dict[str, Any] = None) -> RuntimeReport:
        report = RuntimeReport(report_type)
        if data:
            report.data = dict(data)
        self._reports.append(report)
        return report

    def get_recent(self, count: int = 5) -> List[RuntimeReport]:
        return self._reports[-count:]

    def get_stats(self) -> Dict[str, Any]:
        return {"total_reports": len(self._reports)}
