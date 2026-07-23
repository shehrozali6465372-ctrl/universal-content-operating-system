"""BIManager — Master integrator for all 10 Business Intelligence modules."""
from __future__ import annotations
import threading
import time
from typing import Any, Dict, List, Optional

from .ceo_dashboard import CEODashboard, get_ceo_dashboard
from .revenue_forecasting import RevenueForecasting, get_revenue_forecasting
from .niche_dashboard import NicheDashboard, get_niche_dashboard
from .platform_dashboard import PlatformDashboard, get_platform_dashboard
from .ai_dashboard import AIDashboard, get_ai_dashboard
from .empire_dashboard import EmpireDashboard, get_empire_dashboard
from .alert_center import AlertCenter, get_alert_center
from .executive_reports import ExecutiveReports, get_executive_reports
from .api_dashboard import APIDashboard, get_api_dashboard


class BIManager:
    """Master integrator for Enterprise Analytics & Business Intelligence."""
    _instance: Optional["BIManager"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "BIManager":
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
        self._ceo = get_ceo_dashboard()
        self._forecasting = get_revenue_forecasting()
        self._niche = get_niche_dashboard()
        self._platform = get_platform_dashboard()
        self._ai = get_ai_dashboard()
        self._empire = get_empire_dashboard()
        self._alerts = get_alert_center()
        self._reports = get_executive_reports()
        self._api = get_api_dashboard()
        self._initialized_at = time.time()

    @property
    def ceo(self) -> CEODashboard:
        return self._ceo

    @property
    def forecasting(self) -> RevenueForecasting:
        return self._forecasting

    @property
    def niche(self) -> NicheDashboard:
        return self._niche

    @property
    def platform(self) -> PlatformDashboard:
        return self._platform

    @property
    def ai(self) -> AIDashboard:
        return self._ai

    @property
    def empire(self) -> EmpireDashboard:
        return self._empire

    @property
    def alerts(self) -> AlertCenter:
        return self._alerts

    @property
    def reports(self) -> ExecutiveReports:
        return self._reports

    @property
    def api(self) -> APIDashboard:
        return self._api

    def generate_daily_report(self) -> Dict[str, Any]:
        ceo = self._ceo.get_ceo_summary()
        niche = self._niche.get_dashboard()
        platform = self._platform.get_dashboard()
        ai = self._ai.get_dashboard()
        empire = self._empire.get_dashboard()
        alert_summary = self._alerts.get_alert_summary()
        report_data = {
            "report_type": "daily",
            "date": time.strftime("%Y-%m-%d"),
            "ceo_summary": ceo,
            "niche_summary": {"total_niches": niche["total_niches"],
                             "total_revenue": niche["total_revenue"]},
            "platform_summary": {"total_platforms": platform["total_platforms"],
                                "total_revenue": platform["total_revenue"]},
            "ai_health": ai["current"]["overall_health"],
            "empire_health": empire["current"]["health_rate"],
            "active_alerts": alert_summary["active"],
        }
        report = self._reports.generate_report(
            "daily", time.strftime("%Y-%m-%d"), data=report_data,
        )
        return {"report": report.to_dict(), "data": report_data}

    def get_full_bi_status(self) -> Dict[str, Any]:
        return {
            "overall": "Active",
            "uptime_seconds": round(time.time() - self._initialized_at, 2),
            "ceo": self._ceo.get_ceo_summary(),
            "forecasting": self._forecasting.get_full_forecast(),
            "niche": self._niche.get_dashboard(),
            "platform": self._platform.get_dashboard(),
            "ai": self._ai.get_dashboard(),
            "empire": self._empire.get_dashboard(),
            "alerts": self._alerts.get_alert_summary(),
            "reports": self._reports.get_reports_status(),
            "api": self._api.get_api_status(),
        }

    def get_executive_summary(self) -> Dict[str, Any]:
        ceo = self._ceo.get_ceo_summary()
        niche = self._niche.get_dashboard()
        platform = self._platform.get_dashboard()
        ai = self._ai.get_dashboard()
        empire = self._empire.get_dashboard()
        alerts = self._alerts.get_alert_summary()
        return {
            "total_revenue": ceo.get("total_revenue", 0),
            "total_profit": ceo.get("total_profit", 0),
            "total_accounts": empire["current"]["total_accounts"],
            "active_accounts": empire["current"]["active_accounts"],
            "total_niches": niche["total_niches"],
            "total_platforms": platform["total_platforms"],
            "ai_health": ai["current"]["overall_health"],
            "empire_health_rate": empire["current"]["health_rate"],
            "active_alerts": alerts["active"],
            "critical_alerts": alerts["critical_active"],
        }

    def stats(self) -> Dict[str, Any]:
        return {
            "ceo": self._ceo.stats(),
            "forecasting": self._forecasting.stats(),
            "niche": self._niche.stats(),
            "platform": self._platform.stats(),
            "ai": self._ai.stats(),
            "empire": self._empire.stats(),
            "alerts": self._alerts.stats(),
            "reports": self._reports.stats(),
            "api": self._api.stats(),
        }


def get_bi_manager() -> BIManager:
    return BIManager()
