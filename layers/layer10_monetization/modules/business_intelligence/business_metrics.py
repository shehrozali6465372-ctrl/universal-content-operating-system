"""BusinessMetrics — bounded, validated business observations."""
from __future__ import annotations
from typing import Any, Dict, List


class BusinessMetrics:
    def __init__(self, max_records: int = 10000) -> None:
        if max_records <= 0:
            raise ValueError("max_records must be positive")
        self._max_records = max_records
        self._records: List[Dict[str, Any]] = []

    def record(self, revenue_growth: float = 0.0, profit: float = 0.0,
               conversion_rate: float = 0.0, customer_count: int = 0,
               retention_rate: float = 0.0, churn_rate: float = 0.0,
               arpu: float = 0.0, roi: float = 0.0) -> Dict[str, Any]:
        if customer_count < 0 or any(rate < 0 for rate in
                                     (conversion_rate, retention_rate, churn_rate)):
            raise ValueError("invalid metric values")
        entry = {"revenue_growth": revenue_growth, "profit": profit,
                 "conversion_rate": conversion_rate, "customer_count": customer_count,
                 "retention_rate": retention_rate, "churn_rate": churn_rate,
                 "arpu": arpu, "roi": roi}
        self._records.append(entry)
        if len(self._records) > self._max_records:
            del self._records[:-self._max_records]
        return dict(entry)

    def get_latest(self) -> Dict[str, Any]:
        return dict(self._records[-1]) if self._records else {}

    def get_average(self) -> Dict[str, float]:
        if not self._records:
            return {}
        fields = ("revenue_growth", "profit", "conversion_rate", "retention_rate",
                  "churn_rate", "arpu", "roi")
        return {field: round(sum(r.get(field, 0.0) for r in self._records) / len(self._records), 4)
                for field in fields}

    def get_trend(self, metric: str = "revenue_growth", count: int = 10) -> List[float]:
        return [r.get(metric, 0.0) for r in self._records[-max(0, count):]]

    def get_growth_direction(self, metric: str = "revenue_growth") -> str:
        if len(self._records) < 2:
            return "insufficient_data"
        current = self._records[-1].get(metric, 0.0)
        previous = self._records[-2].get(metric, 0.0)
        return "improving" if current > previous else "declining" if current < previous else "stable"

    def get_summary(self) -> Dict[str, Any]:
        return {"total_records": len(self._records), "latest": self.get_latest(),
                "average": self.get_average()}

    def get_stats(self) -> Dict[str, Any]:
        return {"total_records": len(self._records)}
