"""TaskReport — Generate task reports."""
from __future__ import annotations
import time
from typing import Any, Dict, List
class TaskReport:
    def __init__(self, report_type: str="summary"):
        self.report_id = f"trpt_{int(time.time())}"; self.report_type = report_type; self.data: Dict[str, Any] = {}
    def to_dict(self) -> Dict[str, Any]: return {"report_id": self.report_id, "type": self.report_type, "data": self.data}

class TaskReportGenerator:
    def __init__(self): self._reports: List[TaskReport] = []
    def generate(self, report_type: str="summary", data: Dict[str, Any]=None) -> TaskReport:
        r = TaskReport(report_type)
        if data: r.data = dict(data)
        self._reports.append(r)
        return r
    def get_recent(self, count: int=5) -> List[TaskReport]: return self._reports[-count:]
    def get_stats(self) -> Dict[str, Any]: return {"total": len(self._reports)}
