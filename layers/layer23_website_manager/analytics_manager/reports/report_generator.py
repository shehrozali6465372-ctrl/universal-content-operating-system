"""ReportGenerator — Generate daily, weekly, monthly, executive reports."""
from __future__ import annotations
import time
import json
from typing import Any, Dict, List, Optional
from layers.layer23_website_manager.analytics_manager.models.analytics_models import AnalyticsReport


class ReportGenerator:
    def __init__(self):
        self._reports: List[AnalyticsReport] = []

    def generate_report(self, report_type: str, data: Dict[str, Any],
                         period: str = "") -> AnalyticsReport:
        report = AnalyticsReport(report_type=report_type, period=period or report_type, data=data)
        self._reports.append(report)
        return report

    def generate_daily_report(self, summary: Dict[str, Any]) -> AnalyticsReport:
        return self.generate_report("daily", summary, "24h")

    def generate_weekly_report(self, summary: Dict[str, Any]) -> AnalyticsReport:
        return self.generate_report("weekly", summary, "7d")

    def generate_monthly_report(self, summary: Dict[str, Any]) -> AnalyticsReport:
        return self.generate_report("monthly", summary, "30d")

    def generate_executive_report(self, kpis: List[Any], insights: List[Any],
                                    trends: List[Any]) -> AnalyticsReport:
        data = {"kpis": [k.to_dict() if hasattr(k, 'to_dict') else k for k in kpis],
                "insights": [i.to_dict() if hasattr(i, 'to_dict') else i for i in insights],
                "trends": [t.to_dict() if hasattr(t, 'to_dict') else t for t in trends]}
        return self.generate_report("executive", data, "overview")

    def get_stats(self) -> Dict[str, int]:
        return {"total_reports": len(self._reports)}
