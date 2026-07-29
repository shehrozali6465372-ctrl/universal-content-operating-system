"""FinancialDashboard — Display revenue today, this month, total, profit, expenses, net income."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional


class FinancialDashboard:
    def generate(self, total_revenue: float, total_commission: float, total_expenses: float,
                  source_breakdown: List[Dict], top_products: List[Dict],
                  top_merchants: List[Dict], forecasts: List[Dict]) -> Dict[str, Any]:
        net_income = total_revenue - total_expenses
        profit_margin = ((total_revenue - total_expenses) / max(total_revenue, 1)) * 100
        return {
            "summary": {"total_revenue": round(total_revenue, 2), "total_commission": round(total_commission, 2),
                "total_expenses": round(total_expenses, 2), "net_income": round(net_income, 2),
                "profit_margin": round(profit_margin, 1)},
            "sources": [{"name": s.name if hasattr(s, 'name') else s.get("name", ""), "revenue": round(s.total_revenue if hasattr(s, 'total_revenue') else s.get("total_revenue", 0), 2)} for s in source_breakdown[:5]],
            "top_products": [{"name": p.get("product_name", "") if isinstance(p, dict) else p.get("product_name", ""), "revenue": round(p.get("revenue", 0) if isinstance(p, dict) else 0, 2)} for p in top_products[:5]],
            "top_merchants": [{"name": m.get("merchant_name", "") if isinstance(m, dict) else m.get("merchant_name", ""), "revenue": round(m.get("revenue", 0) if isinstance(m, dict) else 0, 2)} for m in top_merchants[:5]],
            "forecasts": forecasts[:3], "generated_at": time.time(),
        }

    def get_stats(self) -> Dict: return {"total_dashboards": 1}
