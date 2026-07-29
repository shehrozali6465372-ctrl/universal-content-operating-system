"""MerchantRevenueAnalyzer — Analyze merchant performance, conversion, ROI."""
from __future__ import annotations
import time, threading
from typing import Any, Dict, List, Optional


class MerchantRevenueAnalyzer:
    def __init__(self):
        self._merchants: Dict[str, Dict] = {}
        self._lock = threading.Lock()

    def record_merchant(self, merchant_name: str, category: str = "", sales: int = 0,
                         revenue: float = 0.0, commission: float = 0.0, clicks: int = 0):
        with self._lock:
            if merchant_name not in self._merchants:
                self._merchants[merchant_name] = {"merchant_name": merchant_name, "category": category,
                    "sales": 0, "revenue": 0.0, "commission": 0.0, "clicks": 0}
            m = self._merchants[merchant_name]
            m["sales"] += sales; m["revenue"] += revenue; m["commission"] += commission; m["clicks"] += clicks

    def get_best_merchants(self, top_k: int = 5) -> List[Dict]:
        return sorted(self._merchants.values(), key=lambda m: m["revenue"], reverse=True)[:top_k]

    def get_summary(self) -> Dict:
        ms = list(self._merchants.values())
        return {"total_merchants": len(ms), "total_revenue": round(sum(m["revenue"] for m in ms), 2),
                "total_commission": round(sum(m["commission"] for m in ms), 2)}

    def get_stats(self) -> Dict: return {"total_merchants": len(self._merchants)}
