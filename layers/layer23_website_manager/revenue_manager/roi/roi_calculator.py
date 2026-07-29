"""ROICalculator — Calculate ROI, ROAS, profit margin, cost per visitor, cost per sale."""
from __future__ import annotations
from typing import Any, Dict, List, Optional


class ROICalculator:
    def calculate(self, revenue: float, cost: float, visitors: int = 0, sales: int = 0) -> Dict[str, float]:
        roi = ((revenue - cost) / max(cost, 1)) * 100
        roas = revenue / max(cost, 1)
        profit_margin = ((revenue - cost) / max(revenue, 1)) * 100
        cost_per_visitor = cost / max(visitors, 1)
        cost_per_sale = cost / max(sales, 1)
        return {"roi": round(roi, 1), "roas": round(roas, 2), "profit_margin": round(profit_margin, 1),
                "cost_per_visitor": round(cost_per_visitor, 4), "cost_per_sale": round(cost_per_sale, 2)}

    def get_stats(self) -> Dict: return {"total_calculations": 1}
