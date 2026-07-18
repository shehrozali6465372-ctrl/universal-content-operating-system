"""BusinessIntelligenceAPI — Universal API for business data and insights."""
from __future__ import annotations
from typing import Any, Dict, List

from layers.layer10_monetization.modules.business_intelligence.revenue_tracker import RevenueTracker
from layers.layer10_monetization.modules.business_intelligence.roi_analyzer import ROIAnalyzer
from layers.layer10_monetization.modules.business_intelligence.campaign_manager import CampaignManager
from layers.layer10_monetization.modules.business_intelligence.budget_planner import BudgetPlanner
from layers.layer10_monetization.modules.business_intelligence.business_forecaster import BusinessForecaster
from layers.layer10_monetization.modules.business_intelligence.business_metrics import BusinessMetrics


class BusinessIntelligenceAPI:
    """Universal API for revenue data, ROI, forecasts, and growth recommendations."""

    def __init__(self) -> None:
        self.revenue_tracker = RevenueTracker()
        self.roi_analyzer = ROIAnalyzer()
        self.campaign_manager = CampaignManager()
        self.budget_planner = BudgetPlanner()
        self.forecaster = BusinessForecaster()
        self.metrics = BusinessMetrics()

    def get_revenue(self, platform: str = "") -> Dict[str, Any]:
        return {"total": self.revenue_tracker.get_total_revenue(platform),
                "daily": self.revenue_tracker.get_daily_revenue(platform),
                "weekly": self.revenue_tracker.get_weekly_revenue(platform),
                "monthly": self.revenue_tracker.get_monthly_revenue(platform),
                "breakdown": self.revenue_tracker.get_revenue_breakdown(platform)}

    def get_roi(self, platform: str = "") -> Dict[str, Any]:
        snapshot = self.roi_analyzer.get_latest(platform)
        if snapshot:
            return snapshot.to_dict()
        return {"roi": 0.0, "roas": 0.0, "platform": platform}

    def get_campaigns(self, status: str = "") -> List[Dict[str, Any]]:
        if status == "active":
            return [c.to_dict() for c in self.campaign_manager.get_active()]
        return [c.to_dict() for c in self.campaign_manager.get_top_performing()]

    def get_budget_status(self) -> Dict[str, Any]:
        return {"total_spent": self.budget_planner.get_total_spent(),
                "total_remaining": self.budget_planner.get_total_remaining(),
                "utilization": self.budget_planner.get_utilization_report()}

    def get_forecast(self, metric: str = "revenue") -> Dict[str, Any]:
        forecast = self.forecaster.get_latest_forecast(metric)
        if forecast:
            return forecast.to_dict()
        return {"metric": metric, "predicted_value": 0.0}

    def get_growth_recommendations(self) -> List[str]:
        recs: List[str] = []
        latest = self.metrics.get_latest()
        if latest:
            if latest.get("conversion_rate", 0) < 0.02:
                recs.append("Optimize conversion funnel")
            if latest.get("retention_rate", 0) < 0.7:
                recs.append("Focus on customer retention")
            if latest.get("churn_rate", 0) > 0.1:
                recs.append("Address churn — analyze loss causes")
            if latest.get("arpu", 0) < 10:
                recs.append("Explore upsell opportunities")
        if not recs:
            recs.append("Metrics look healthy — continue current strategy")
        return recs

    def get_health(self) -> Dict[str, Any]:
        return {"revenue_tracker": self.revenue_tracker.get_stats(),
                "roi_analyzer": self.roi_analyzer.get_stats(),
                "campaign_manager": self.campaign_manager.get_stats(),
                "budget_planner": self.budget_planner.get_stats(),
                "forecaster": self.forecaster.get_stats(),
                "metrics": self.metrics.get_stats()}

    def to_dict(self) -> Dict[str, Any]:
        return {"revenue": self.get_revenue(),
                "roi": self.get_roi(),
                "budget": self.get_budget_status(),
                "forecast": self.get_forecast(),
                "recommendations": self.get_growth_recommendations()}
