"""BusinessMetrics — Track revenue growth, profit, conversion, and retention."""
from __future__ import annotations
from typing import Any, Dict, List


class BusinessMetrics:
    """Track revenue growth, profit, conversion rate, retention, churn, and ARPU."""

    def __init__(self) -> None:
        self._records: List[Dict[str, Any]] = []

    def record(self, revenue_growth: float = 0.0, profit: float = 0.0,
               conversion_rate: float = 0.0, customer_count: int = 0,
               retention_rate: float = 0.0, churn_rate: float = 0.0,
               arpu: float = 0.0, roi: float = 0.0) -> Dict[str, Any]:
        entry = {
            "revenue_growth": revenue_growth, "profit": profit,
            "conversion_rate": conversion_rate, "customer_count": customer_count,
            "retention_rate": retention_rate, "churn_rate": churn_rate,
            "arpu": arpu, "roi": roi,
        }
        self._records.append(entry)
        return entry

    def get_latest(self) -> Dict[str, Any]:
        return self._records[-1] if self._records else {}

    def get_average(self) -> Dict[str, float]:
        if not self._records:
            return {}
        metrics = ["revenue_growth", "profit", "conversion_rate",
                    "retention_rate", "churn_rate", "arpu", "roi"]
        result: Dict[str, float] = {}
        for m in metrics:
            values = [r.get(m, 0.0) for r in self._records]
            result[m] = round(sum(values) / len(values), 4)
        return result

    def get_trend(self, metric: str = "revenue_growth",
                  count: int = 10) -> List[float]:
        return [r.get(metric, 0.0) for r in self._records[-count:]]

    def get_growth_direction(self, metric: str = "revenue_growth") -> str:
        if len(self._records) < 2:
            return "insufficient_data"
        recent = self._records[-1].get(metric, 0.0)
        previous = self._records[-2].get(metric, 0.0)
        if recent > previous:
            return "improving"
        elif recent < previous:
            return "declining"
        return "stable"

    def get_summary(self) -> Dict[str, Any]:
        latest = self.get_latest()
        avg = self.get_average()
        return {"total_records": len(self._records), "latest": latest,
                "average": avg}

    def get_stats(self) -> Dict[str, Any]:
        return {"total_records": len(self._records)}
