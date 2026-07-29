"""RevenueManager — Layer 23 / Module 10.

Revenue Intelligence Engine: track, analyze, forecast, and optimize all revenue streams.
Flow: Traffic → Click → Sale → Commission → Revenue → Forecast → Optimization
"""
from __future__ import annotations
import time, threading
from typing import Any, Dict, List, Optional
from layers.layer23_website_manager.revenue_manager.models.revenue_models import (
    RevenueSource, CommissionRecord, RevenueTransaction, RevenueSummary, Budget,
    RevenueForecast, RevenueAlert, FinancialReport, RevenuePeriod, TransactionStatus, AlertSeverity,
)
from layers.layer23_website_manager.revenue_manager.sources.revenue_source_manager import RevenueSourceManager
from layers.layer23_website_manager.revenue_manager.commissions.commission_tracker import CommissionTracker
from layers.layer23_website_manager.revenue_manager.attribution.revenue_attribution_engine import RevenueAttributionEngine
from layers.layer23_website_manager.revenue_manager.products.product_revenue_analyzer import ProductRevenueAnalyzer
from layers.layer23_website_manager.revenue_manager.merchants.merchant_revenue_analyzer import MerchantRevenueAnalyzer
from layers.layer23_website_manager.revenue_manager.roi.roi_calculator import ROICalculator
from layers.layer23_website_manager.revenue_manager.forecasting.revenue_forecast_engine import RevenueForecastEngine
from layers.layer23_website_manager.revenue_manager.optimization.revenue_optimizer import RevenueOptimizer
from layers.layer23_website_manager.revenue_manager.budgets.budget_manager import BudgetManager
from layers.layer23_website_manager.revenue_manager.dashboard.financial_dashboard import FinancialDashboard
from layers.layer23_website_manager.revenue_manager.alerts.revenue_alert_manager import RevenueAlertManager
from layers.layer23_website_manager.revenue_manager.reports.financial_reports import FinancialReports
from layers.layer23_website_manager.revenue_manager.api.revenue_api import RevenueAPI


class RevenueManager:
    def __init__(self):
        self._lock = threading.RLock(); self._start_time = time.time()
        self.sources = RevenueSourceManager()
        self.commissions = CommissionTracker()
        self.attribution = RevenueAttributionEngine()
        self.products = ProductRevenueAnalyzer()
        self.merchants = MerchantRevenueAnalyzer()
        self.roi_calc = ROICalculator()
        self.forecast_engine = RevenueForecastEngine()
        self.optimizer = RevenueOptimizer()
        self.budgets = BudgetManager()
        self.dashboard_mgr = FinancialDashboard()
        self.alerts = RevenueAlertManager()
        self.reports = FinancialReports()
        self.api = RevenueAPI(self)
        self._transactions: List[RevenueTransaction] = []
        self._total_revenue = 0.0; self._total_expenses = 0.0; self._total_operations = 0

    def initialize(self) -> Dict:
        srcs = self.sources.load_presets(); buds = self.budgets.load_presets()
        return {"sources_loaded": len(srcs), "budgets_loaded": len(buds)}

    def record_transaction(self, source_id: str, merchant: str = "", product_id: str = "",
                            article_id: str = "", pin_id: str = "", sale_amount: float = 0.0,
                            commission: float = 0.0, fee: float = 0.0) -> RevenueTransaction:
        t = RevenueTransaction(source_id=source_id, merchant=merchant, product_id=product_id,
            article_id=article_id, pin_id=pin_id, sale_amount=sale_amount, commission=commission, fee=fee)
        self._transactions.append(t)
        self.sources.record_revenue(source_id, sale_amount, commission)
        self.products.record_product(product_id, merchant=merchant, sales=1, revenue=sale_amount, commission=commission)
        self.merchants.record_merchant(merchant, sales=1, revenue=sale_amount, commission=commission)
        self._total_revenue += sale_amount; self._total_expenses += fee
        attr = self.attribution.attribute(article_id=article_id, pin_id=pin_id,
            product_id=product_id, merchant=merchant, sale_amount=sale_amount, commission=commission)
        self._log("record_transaction", {}); return t

    def record_commission(self, source_id: str, amount: float, sale_amount: float, rate: float) -> CommissionRecord:
        return self.commissions.record_commission(source_id, amount, sale_amount, rate)

    def calculate_roi(self, revenue: float = 0, cost: float = 0, visitors: int = 0, sales: int = 0) -> Dict:
        return self.roi_calc.calculate(revenue or self._total_revenue, cost or self._total_expenses, visitors, sales)

    def forecast(self, period: RevenuePeriod = RevenuePeriod.MONTHLY, growth_rate: float = 0.05) -> RevenueForecast:
        daily_avg = self._total_revenue / max((time.time() - self._start_time) / 86400, 1)
        return self.forecast_engine.forecast(daily_avg, growth_rate, period)

    def get_optimization(self) -> Dict:
        return self.optimizer.analyze(self.products.get_summary(), self.merchants.get_summary(),
                                       self._total_revenue, self._total_expenses)

    def record_spend(self, budget_id: str, amount: float) -> bool:
        return self.budgets.record_spend(budget_id, amount)

    def check_anomaly(self, current: float = 0, previous: float = 0) -> Optional[RevenueAlert]:
        return self.alerts.check_revenue_anomaly(current or self._total_revenue, previous)

    def get_dashboard(self) -> Dict:
        return self.dashboard_mgr.generate(self._total_revenue, sum(t.commission for t in self._transactions),
            self._total_expenses, self.sources.get_all_sources(), self.products.get_best_products(),
            self.merchants.get_best_merchants(), [self.forecast().to_dict()])

    def generate_report(self, report_type: str = "daily") -> FinancialReport:
        summary = {"total_revenue": round(self._total_revenue, 2), "total_expenses": round(self._total_expenses, 2),
            "net_income": round(self._total_revenue - self._total_expenses, 2),
            "transactions": len(self._transactions), "sources": self.sources.get_stats(),
            "products": self.products.get_summary(), "merchants": self.merchants.get_summary()}
        generators = {"daily": self.reports.generate_daily, "weekly": self.reports.generate_weekly,
                       "monthly": self.reports.generate_monthly, "yearly": self.reports.generate_yearly}
        return generators.get(report_type, self.reports.generate_daily)(summary)

    def simulate_revenue(self, days: int = 7) -> Dict:
        import random
        sources = self.sources.get_all_sources()
        merchants_list = ["Amazon", "Nike", "Wayfair", "Sephora", "Walmart"]
        for d in range(days):
            for _ in range(random.randint(2, 8)):
                src = random.choice(sources) if sources else None
                if not src: continue
                sale = random.uniform(10, 200)
                comm = sale * (src.commission_rate / 100)
                self.record_transaction(src.source_id, random.choice(merchants_list),
                    f"prod_{random.randint(1,5)}", f"art_{random.randint(1,3)}", sale_amount=sale, commission=comm, fee=sale*0.05)
        return {"simulated": True, "transactions": len(self._transactions)}

    def get_status(self) -> Dict:
        return {"module": "Revenue Manager (Layer 23 / Module 10)", "version": "1.0.0", "overall": "Healthy",
            "uptime_seconds": round(time.time() - self._start_time, 1),
            "total_revenue": round(self._total_revenue, 2), "total_expenses": round(self._total_expenses, 2),
            "net_income": round(self._total_revenue - self._total_expenses, 2),
            "transactions": len(self._transactions),
            "sources": self.sources.get_stats(), "commissions": self.commissions.get_stats(),
            "products": self.products.get_stats(), "merchants": self.merchants.get_stats(),
            "budgets": self.budgets.get_stats(), "alerts": self.alerts.get_stats(),
            "roi": self.roi_calc.get_stats(), "operations": {"total": self._total_operations}}

    def _log(self, op: str, d: dict) -> None:
        with self._lock: self._total_operations += 1


_revenue_manager_instance = None; _instance_lock = threading.Lock()
def get_revenue_manager():
    global _revenue_manager_instance
    if _revenue_manager_instance is None:
        with _instance_lock:
            if _revenue_manager_instance is None: _revenue_manager_instance = RevenueManager()
    return _revenue_manager_instance
