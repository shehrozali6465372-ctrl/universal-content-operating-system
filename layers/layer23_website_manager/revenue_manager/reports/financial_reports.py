"""FinancialReports — Generate daily, weekly, monthly, yearly reports and tax summary."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional
from layers.layer23_website_manager.revenue_manager.models.revenue_models import FinancialReport


class FinancialReports:
    def __init__(self):
        self._reports: List[FinancialReport] = []

    def generate(self, report_type: str, data: Dict[str, Any], period: str = "") -> FinancialReport:
        r = FinancialReport(report_type=report_type, period=period or report_type, data=data)
        self._reports.append(r); return r

    def generate_daily(self, summary: Dict) -> FinancialReport: return self.generate("daily", summary, "24h")
    def generate_weekly(self, summary: Dict) -> FinancialReport: return self.generate("weekly", summary, "7d")
    def generate_monthly(self, summary: Dict) -> FinancialReport: return self.generate("monthly", summary, "30d")
    def generate_yearly(self, summary: Dict) -> FinancialReport: return self.generate("yearly", summary, "365d")
    def generate_tax_summary(self, revenue: float, expenses: float) -> FinancialReport:
        return self.generate("tax", {"gross_revenue": round(revenue, 2), "total_expenses": round(expenses, 2),
            "net_income": round(revenue - expenses, 2), "estimated_tax": round((revenue - expenses) * 0.25, 2)})

    def get_stats(self) -> Dict: return {"total_reports": len(self._reports)}
