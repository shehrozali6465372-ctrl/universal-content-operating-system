"""CostValidator — validate cost data and budgets."""
from __future__ import annotations
from typing import Any, Dict, List
from .models import CostEntry, BudgetLimit

class CostValidator:
    def validate_entry(self, entry: CostEntry) -> Dict[str, Any]:
        issues: List[str] = []
        if entry.cost_usd < 0: issues.append("Negative cost")
        if entry.prompt_tokens < 0: issues.append("Negative prompt tokens")
        if entry.completion_tokens < 0: issues.append("Negative completion tokens")
        if entry.cost_usd > 1000: issues.append("Cost exceeds $1000")
        return {"valid": len(issues) == 0, "issues": issues}
    def validate_budget(self, amount: float, limit: BudgetLimit) -> Dict[str, Any]:
        issues: List[str] = []
        if amount > limit.daily: issues.append("Exceeds daily budget")
        return {"valid": len(issues) == 0, "issues": issues}
