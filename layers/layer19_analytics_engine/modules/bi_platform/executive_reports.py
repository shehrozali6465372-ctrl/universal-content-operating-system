"""ExecutiveReports — Auto-generated daily/weekly/monthly/quarterly reports."""
from __future__ import annotations
import threading
import time
import uuid
from typing import Any, Dict, List, Optional


class Report:
    __slots__ = ("id", "report_type", "period", "generated_at", "data",
                 "format", "status", "sections")

    def __init__(self, report_type: str, period: str) -> None:
        self.id = str(uuid.uuid4())[:12]
        self.report_type = report_type
        self.period = period
        self.generated_at = time.time()
        self.data: Dict[str, Any] = {}
        self.format = "json"
        self.status = "generated"
        self.sections: List[Dict[str, Any]] = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id, "type": self.report_type,
            "period": self.period, "generated": self.generated_at,
            "sections": len(self.sections), "status": self.status,
        }


class ExecutiveReports:
    """Generates and stores executive reports: daily, weekly, monthly, quarterly."""
    _instance: Optional["ExecutiveReports"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "ExecutiveReports":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True
        self._reports: Dict[str, Report] = {}
        self._type_index: Dict[str, List[str]] = {}

    def generate_report(self, report_type: str, period: str,
                        sections: List[Dict[str, Any]] = None,
                        data: Dict[str, Any] = None) -> Report:
        report = Report(report_type, period)
        if sections:
            report.sections = sections
        if data:
            report.data = data
        self._reports[report.id] = report
        self._type_index.setdefault(report_type, []).append(report.id)
        return report

    def get_report(self, rid: str) -> Optional[Report]:
        return self._reports.get(rid)

    def get_by_type(self, report_type: str) -> List[Report]:
        ids = self._type_index.get(report_type, [])
        return sorted(
            [self._reports[i] for i in ids if i in self._reports],
            key=lambda r: r.generated_at, reverse=True,
        )

    def get_latest(self, report_type: str = "") -> Optional[Report]:
        if report_type:
            reports = self.get_by_type(report_type)
        else:
            reports = sorted(self._reports.values(), key=lambda r: r.generated_at, reverse=True)
        return reports[0] if reports else None

    def get_reports_status(self) -> Dict[str, Any]:
        reports = list(self._reports.values())
        return {
            "total_reports": len(reports),
            "by_type": {t: len(ids) for t, ids in self._type_index.items()},
            "latest": self.get_latest().to_dict() if self.get_latest() else None,
        }

    def stats(self) -> Dict[str, Any]:
        return {
            "reports": len(self._reports),
            "types": len(self._type_index),
        }


def get_executive_reports() -> ExecutiveReports:
    return ExecutiveReports()
