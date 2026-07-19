"""BudgetManager — manage daily, weekly, monthly budgets."""
from __future__ import annotations
import time
from typing import Any, Dict, List
from .models import BudgetLimit

class BudgetManager:
    def __init__(self, limit: BudgetLimit | None = None) -> None:
        self.limit = limit or BudgetLimit()
        self._daily_spent: Dict[str, float] = {}
        self._alerts: List[Dict[str, Any]] = []
    def can_spend(self, amount: float) -> bool:
        if self.is_over_daily():
            return False
        if self.today_spent() + amount > self.limit.daily and self.limit.hard_stop:
            self._alerts.append({"type": "budget_exceeded", "amount": amount})
            return False
        return True
    def record_spend(self, amount: float) -> None:
        day = time.strftime("%Y-%m-%d")
        self._daily_spent[day] = self._daily_spent.get(day, 0.0) + amount
    def today_spent(self) -> float:
        return self._daily_spent.get(time.strftime("%Y-%m-%d"), 0.0)
    def is_over_daily(self) -> bool:
        return self.today_spent() > self.limit.daily
    def remaining_daily(self) -> float:
        return max(0.0, self.limit.daily - self.today_spent())
    def budget_usage_pct(self) -> float:
        return self.today_spent() / self.limit.daily * 100 if self.limit.daily else 0.0
    def get_alerts(self) -> List[Dict[str, Any]]:
        return list(self._alerts)
    def to_dict(self) -> Dict[str, Any]:
        return {**self.limit.to_dict(), "today_spent": round(self.today_spent(), 6),
                "remaining": round(self.remaining_daily(), 6), "usage_pct": round(self.budget_usage_pct(), 2)}
