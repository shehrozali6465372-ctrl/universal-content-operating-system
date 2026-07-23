"""Enterprise Analytics & Business Intelligence Platform — Phase 12."""
from .bi_manager import BIManager, get_bi_manager
from .ceo_dashboard import CEODashboard, get_ceo_dashboard
from .revenue_forecasting import RevenueForecasting, get_revenue_forecasting
from .niche_dashboard import NicheDashboard, get_niche_dashboard
from .platform_dashboard import PlatformDashboard, get_platform_dashboard
from .ai_dashboard import AIDashboard, get_ai_dashboard
from .empire_dashboard import EmpireDashboard, get_empire_dashboard
from .alert_center import AlertCenter, get_alert_center
from .executive_reports import ExecutiveReports, get_executive_reports
from .api_dashboard import APIDashboard, get_api_dashboard

__all__ = [
    "BIManager", "get_bi_manager",
    "CEODashboard", "get_ceo_dashboard",
    "RevenueForecasting", "get_revenue_forecasting",
    "NicheDashboard", "get_niche_dashboard",
    "PlatformDashboard", "get_platform_dashboard",
    "AIDashboard", "get_ai_dashboard",
    "EmpireDashboard", "get_empire_dashboard",
    "AlertCenter", "get_alert_center",
    "ExecutiveReports", "get_executive_reports",
    "APIDashboard", "get_api_dashboard",
]
