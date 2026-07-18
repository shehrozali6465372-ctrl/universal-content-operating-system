"""BusinessOrchestrator — Complete business intelligence pipeline."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional

from layers.layer10_monetization.modules.business_intelligence.revenue_tracker import RevenueTracker
from layers.layer10_monetization.modules.business_intelligence.roi_analyzer import ROIAnalyzer
from layers.layer10_monetization.modules.business_intelligence.campaign_manager import CampaignManager
from layers.layer10_monetization.modules.business_intelligence.budget_planner import BudgetPlanner
from layers.layer10_monetization.modules.business_intelligence.business_forecaster import BusinessForecaster
from layers.layer10_monetization.modules.business_intelligence.opportunity_detector import OpportunityDetector
from layers.layer10_monetization.modules.business_intelligence.monetization_optimizer import MonetizationOptimizer
from layers.layer10_monetization.modules.business_intelligence.financial_memory import FinancialMemory
from layers.layer10_monetization.modules.business_intelligence.business_metrics import BusinessMetrics
from layers.layer10_monetization.modules.business_intelligence.business_report import BusinessReportGenerator
from layers.layer10_monetization.modules.business_intelligence.business_intelligence_api import BusinessIntelligenceAPI


class BusinessOrchestrator:
    """Complete business pipeline.

    Flow: Revenue → Analytics → ROI → Forecast → Opportunities →
          Budget → Monetization → Campaigns → Memory → Reports → API
    """

    def __init__(self) -> None:
        self.revenue_tracker = RevenueTracker()
        self.roi_analyzer = ROIAnalyzer()
        self.campaign_manager = CampaignManager()
        self.budget_planner = BudgetPlanner()
        self.forecaster = BusinessForecaster()
        self.opportunity_detector = OpportunityDetector()
        self.monetization_optimizer = MonetizationOptimizer()
        self.memory = FinancialMemory()
        self.metrics = BusinessMetrics()
        self.report_generator = BusinessReportGenerator()
        self.api = BusinessIntelligenceAPI()
        self._is_running = False
        self._pipeline_runs: List[Dict[str, Any]] = []

    def start(self) -> bool:
        self._is_running = True
        return True

    def stop(self) -> bool:
        self._is_running = False
        return True

    def run_pipeline(self, platform: str = "",
                     revenue_data: Optional[Dict[str, Any]] = None,
                     campaign_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        start = time.time()
        results: Dict[str, Any] = {"platform": platform, "stages": {}}

        # Stage 1: Revenue Collection
        if revenue_data:
            for rt, amt in revenue_data.items():
                self.revenue_tracker.record(rt, amt, platform)
        results["stages"]["revenue"] = self.revenue_tracker.get_stats()

        # Stage 2: ROI Analysis
        revenue = revenue_data.get("ad_revenue", 0.0) if revenue_data else 0.0
        cost = campaign_data.get("cost", 0.0) if campaign_data else 0.0
        snap = self.roi_analyzer.calculate(platform, revenue, cost)
        results["stages"]["roi"] = snap.to_dict()

        # Stage 3: Forecasting
        forecast = self.forecaster.forecast_revenue("next_month", revenue, 0.1)
        results["stages"]["forecast"] = forecast.to_dict()

        # Stage 4: Opportunity Detection
        self.opportunity_detector.detect("trending_niche", f"Opportunity for {platform}",
                                          platform, revenue * 0.5)
        results["stages"]["opportunities"] = self.opportunity_detector.get_stats()

        # Stage 5: Memory Storage
        self.memory.store("pipeline_run", f"{platform}_{time.time()}",
                          {"revenue": revenue, "roi": snap.roi},
                          confidence=snap.roi + 0.5)
        results["stages"]["memory"] = self.memory.get_stats()

        # Stage 6: Metrics
        self.metrics.record(revenue_growth=0.1, profit=revenue - cost, roi=snap.roi)
        results["stages"]["metrics"] = self.metrics.get_stats()

        # Stage 7: Report
        report = self.report_generator.generate("daily", results)
        results["stages"]["report"] = report.to_dict()

        results["duration_ms"] = round((time.time() - start) * 1000, 1)
        self._pipeline_runs.append(results)
        return results

    def get_health(self) -> Dict[str, Any]:
        return {
            "revenue_tracker": self.revenue_tracker.get_stats(),
            "roi_analyzer": self.roi_analyzer.get_stats(),
            "campaign_manager": self.campaign_manager.get_stats(),
            "budget_planner": self.budget_planner.get_stats(),
            "forecaster": self.forecaster.get_stats(),
            "opportunity_detector": self.opportunity_detector.get_stats(),
            "monetization_optimizer": self.monetization_optimizer.get_stats(),
            "financial_memory": self.memory.get_stats(),
            "business_metrics": self.metrics.get_stats(),
            "report_generator": self.report_generator.get_stats(),
            "pipeline_runs": len(self._pipeline_runs),
            "is_running": self._is_running,
        }

    def get_api(self) -> BusinessIntelligenceAPI:
        return self.api
