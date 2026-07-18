"""LoopReport — Generate loop reports."""
from __future__ import annotations
import time
from typing import Any, Dict, List

class LoopReport:
    def __init__(self, report_type: str = "status") -> None:
        self.report_id = f"lrpt_{int(time.time())}"
        self.report_type = report_type
        self.data: Dict[str, Any] = {}
    def to_dict(self) -> Dict[str, Any]:
        return {"report_id": self.report_id, "type": self.report_type, "data": self.data}

class LoopReportGenerator:
    def __init__(self) -> None:
        self._reports: List[LoopReport] = []
    def generate(self, report_type: str = "status", data: Dict[str, Any] = None) -> LoopReport:
        report = LoopReport(report_type)
        if data: report.data = dict(data)
        self._reports.append(report)
        return report
    def get_recent(self, count: int = 5) -> List[LoopReport]:
        return self._reports[-count:]
    def get_stats(self) -> Dict[str, Any]:
        return {"total": len(self._reports)}
