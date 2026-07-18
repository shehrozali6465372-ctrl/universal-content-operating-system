"""LLMReport — Generate LLM usage reports."""
from __future__ import annotations
import json, time
from typing import Any, Dict, List

class LLMReport:
    def __init__(self, report_type: str = "usage") -> None:
        self.report_id = f"lrpt_{int(time.time())}"
        self.report_type = report_type
        self.data: Dict[str, Any] = {}
        self.insights: List[str] = []
    def add_insight(self, insight: str) -> None:
        self.insights.append(insight)
    def to_dict(self) -> Dict[str, Any]:
        return {"report_id": self.report_id, "type": self.report_type,
                "data": self.data, "insights": self.insights}
    def export_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

class LLMReportGenerator:
    def __init__(self) -> None:
        self._reports: List[LLMReport] = []
    def generate(self, report_type: str = "usage", data: Dict[str, Any] = None) -> LLMReport:
        r = LLMReport(report_type)
        if data: r.data = dict(data)
        self._reports.append(r)
        return r
    def get_recent(self, count: int = 5) -> List[LLMReport]:
        return self._reports[-count:]
    def get_stats(self) -> Dict[str, Any]:
        return {"total": len(self._reports)}
