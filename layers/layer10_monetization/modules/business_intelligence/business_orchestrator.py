"""BusinessOrchestrator — explicit, evidence-based monetization pipeline."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional
from uuid import uuid4

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
    """Run monetization accounting from supplied evidence; never fabricate outcomes."""

    def __init__(self, max_pipeline_runs: int = 10000) -> None:
        if max_pipeline_runs <= 0:
            raise ValueError("max_pipeline_runs must be positive")
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
        self._max_pipeline_runs = max_pipeline_runs

    def start(self) -> bool:
        self._is_running = True
        return True

    def stop(self) -> bool:
        self._is_running = False
        return True

    def run_pipeline(self, platform: str = "",
                     revenue_data: Optional[Dict[str, Any]] = None,
                     campaign_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if not self._is_running:
            raise RuntimeError("business orchestrator must be running")
        start = time.time()
        revenue_data = dict(revenue_data or {})
        campaign_data = dict(campaign_data or {})
        results: Dict[str, Any] = {
            "pipeline_id": f"biz_{uuid4().hex}",
            "platform": platform,
            "stages": {},
            "status": "running",
        }

        for revenue_type, amount in revenue_data.items():
            self.revenue_tracker.record(revenue_type, amount, platform)

        results["stages"]["revenue"] = self.revenue_tracker.get_stats()
        revenue = sum(float(amount) for amount in revenue_data.values())
        cost = float(campaign_data.get("cost", 0.0))
        snapshot = self.roi_analyzer.calculate(platform, revenue, cost)
        results["stages"]["roi"] = snapshot.to_dict()

        # Forecasting is explicitly marked as model output, not observed revenue.
        forecast = self.forecaster.forecast_revenue("next_month", revenue, 0.0)
        results["stages"]["forecast"] = forecast.to_dict()

        # No opportunity is invented from revenue alone. Caller must provide an estimate.
        results["stages"]["opportunities"] = self.opportunity_detector.get_stats()

        confidence = max(0.0, min(1.0, 0.5 + snapshot.roi / 2))
        self.memory.store(
            "pipeline_run", results["pipeline_id"],
            {"revenue": revenue, "roi": snapshot.roi},
            confidence=confidence,
        )
        results["stages"]["memory"] = self.memory.get_stats()

        growth = float(campaign_data.get("revenue_growth", 0.0))
        self.metrics.record(revenue_growth=growth, profit=revenue - cost, roi=snapshot.roi)
        results["stages"]["metrics"] = self.metrics.get_stats()

        report = self.report_generator.generate("daily", results)
        results["stages"]["report"] = report.to_dict()
        results["status"] = "completed"
        results["duration_ms"] = round((time.time() - start) * 1000, 1)
        self._pipeline_runs.append(results)
        if len(self._pipeline_runs) > self._max_pipeline_runs:
            del self._pipeline_runs[:-self._max_pipeline_runs]
        return results

    def get_api(self) -> BusinessIntelligenceAPI:
        return self.api

    def get_health(self) -> Dict[str, Any]:
        return {
            "running": self._is_running,
            "is_running": self._is_running,
            "revenue_tracker": self.revenue_tracker.get_stats(),
            "roi_analyzer": self.roi_analyzer.get_stats(),
            "campaign_manager": self.campaign_manager.get_stats(),
            "budget_planner": self.budget_planner.get_stats(),
            "forecaster": self.forecaster.get_stats(),
            "opportunity_detector": self.opportunity_detector.get_stats(),
            "monetization_optimizer": self.monetization_optimizer.get_stats(),
            "memory": self.memory.get_stats(),
            "financial_memory": self.memory.get_stats(),
            "metrics": self.metrics.get_stats(),
            "reports": self.report_generator.get_stats(),
            "pipeline_runs": len(self._pipeline_runs),
        }
