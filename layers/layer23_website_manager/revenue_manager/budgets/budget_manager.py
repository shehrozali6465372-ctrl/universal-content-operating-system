"""BudgetManager — Manage monthly budgets, marketing costs, tool costs, AI costs, profit."""
from __future__ import annotations
import time, threading
from typing import Any, Dict, List, Optional
from layers.layer23_website_manager.revenue_manager.models.revenue_models import Budget, RevenuePeriod


class BudgetManager:
    PRESETS = [
        {"category": "marketing", "name": "Ad Spend", "allocated": 500.0},
        {"category": "tools", "name": "AI API Costs", "allocated": 200.0},
        {"category": "tools", "name": "Hosting", "allocated": 50.0},
        {"category": "tools", "name": "Domain & Email", "allocated": 20.0},
        {"category": "marketing", "name": "Content Creation", "allocated": 300.0},
    ]

    def __init__(self):
        self._budgets: Dict[str, Budget] = {}
        self._lock = threading.Lock()

    def create_budget(self, category: str, name: str, allocated: float, period: RevenuePeriod = RevenuePeriod.MONTHLY) -> Budget:
        b = Budget(category=category, name=name, allocated=allocated, period=period)
        with self._lock: self._budgets[b.budget_id] = b
        return b

    def load_presets(self) -> List[Budget]:
        return [self.create_budget(p["category"], p["name"], p["allocated"]) for p in self.PRESETS]

    def record_spend(self, budget_id: str, amount: float) -> bool:
        b = self._budgets.get(budget_id)
        if not b: return False
        with self._lock: b.spent += amount; return True

    def get_summary(self) -> Dict[str, Any]:
        budgets = list(self._budgets.values())
        return {"total_budgets": len(budgets), "total_allocated": round(sum(b.allocated for b in budgets), 2),
                "total_spent": round(sum(b.spent for b in budgets), 2),
                "total_remaining": round(sum(b.remaining for b in budgets), 2),
                "avg_usage": round(sum(b.usage_pct for b in budgets) / max(len(budgets), 1), 1)}

    def get_stats(self) -> Dict: s = self.get_summary(); return {"total_budgets": s["total_budgets"]}
