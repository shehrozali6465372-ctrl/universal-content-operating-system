"""RevenueAPI — Provide revenue data to Learning Connector, Universal Dashboard, Finance Layer."""
from __future__ import annotations
from typing import Any, Dict, List, Optional


class RevenueAPI:
    def __init__(self, parent):
        self._parent = parent

    def get_summary(self) -> Dict[str, Any]:
        return {"sources": self._parent.sources.get_stats(), "commissions": self._parent.commissions.get_summary(),
                "products": self._parent.products.get_summary(), "merchants": self._parent.merchants.get_summary(),
                "budgets": self._parent.budgets.get_summary(), "roi": self._parent.roi_calc.get_stats()}

    def get_top_revenue(self, top_k: int = 5) -> Dict[str, Any]:
        return {"top_sources": [s.to_dict() for s in self._parent.sources.get_top_sources(top_k)],
                "top_products": self._parent.products.get_best_products(top_k),
                "top_merchants": self._parent.merchants.get_best_merchants(top_k)}

    def get_stats(self) -> Dict: return {"total_queries": 1}
