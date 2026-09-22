"""RevenueForecasting — 30-day, 90-day, 1-year predictions + ROI forecast."""
from __future__ import annotations
import threading
import time
from typing import Any, Dict, List, Optional


class ForecastPoint:
    __slots__ = ("date", "predicted_revenue", "predicted_profit", "confidence",
                 "lower_bound", "upper_bound", "model", "provenance")

    def __init__(self, date: str, revenue: float = 0.0) -> None:
        self.date = date
        self.predicted_revenue = revenue
        self.predicted_profit = 0.0
        self.confidence = 50.0
        self.lower_bound = revenue * 0.6
        self.upper_bound = revenue * 1.4
        self.model = ""
        self.provenance = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "date": self.date,
            "revenue": round(self.predicted_revenue, 2),
            "profit": round(self.predicted_profit, 2),
            "confidence": round(self.confidence, 1),
            "range": [round(self.lower_bound, 2), round(self.upper_bound, 2)],
            "model": self.model,
            "provenance": self.provenance,
        }


class RevenueForecasting:
    """Predicts revenue for 30, 90, 365 days with confidence intervals."""
    _instance: Optional["RevenueForecasting"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "RevenueForecasting":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True
        self._historical: List[Dict[str, float]] = []
        self._forecasts: Dict[str, List[ForecastPoint]] = {}
        self._roi_forecast: Dict[str, float] = {}

    def add_historical(self, date: str, revenue: float, profit: float = 0.0,
                       expenses: float = 0.0) -> None:
        self._historical.append({
            "date": date, "revenue": revenue,
            "profit": profit if profit else revenue - expenses,
        })

    def forecast_30_days(self) -> List[ForecastPoint]:
        return self._generate_forecast(30, "30day")

    def forecast_90_days(self) -> List[ForecastPoint]:
        return self._generate_forecast(90, "90day")

    def forecast_1_year(self) -> List[ForecastPoint]:
        return self._generate_forecast(365, "1year")

    def _generate_forecast(self, days: int, key: str) -> List[ForecastPoint]:
        if len(self._historical) < 2:
            raise ValueError("revenue forecast requires at least two real historical observations")
        revenues = [float(h["revenue"]) for h in self._historical]
        profits = [float(h["profit"]) for h in self._historical]
        n = len(revenues)
        xs = list(range(n))
        xbar = sum(xs) / n
        ybar = sum(revenues) / n
        denom = sum((x - xbar) ** 2 for x in xs)
        slope = sum((x - xbar) * (y - ybar) for x, y in zip(xs, revenues)) / denom if denom else 0.0
        intercept = ybar - slope * xbar
        residuals = [y - (intercept + slope * x) for x, y in zip(xs, revenues)]
        ss_res = sum(e * e for e in residuals)
        ss_tot = sum((y - ybar) ** 2 for y in revenues)
        r_squared = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
        residual_std = (sum(e * e for e in residuals) / max(1, n - 2)) ** 0.5
        total_revenue = sum(revenues)
        profit_margin = sum(profits) / total_revenue if total_revenue > 0 else 0.0
        confidence_base = max(0.0, min(95.0, 20.0 + min(40.0, n * 2.0) + max(0.0, r_squared) * 35.0))
        model_provenance = {
            "model": "ordinary_least_squares_linear_trend",
            "observation_count": n,
            "r_squared": round(r_squared, 6),
            "historical_start": self._historical[0]["date"],
            "historical_end": self._historical[-1]["date"],
        }
        points = []
        for i in range(1, days + 1):
            day = time.strftime("%Y-%m-%d", time.localtime(time.time() + i * 86400))
            predicted = max(0.0, intercept + slope * (n - 1 + i))
            confidence = max(20.0, confidence_base - (i * 0.2))
            fp = ForecastPoint(day, predicted)
            fp.predicted_profit = predicted * profit_margin
            fp.confidence = confidence
            margin = max(residual_std, abs(predicted) * 0.05)
            fp.lower_bound = max(0.0, predicted - margin * 1.96)
            fp.upper_bound = predicted + margin * 1.96
            fp.model = "ordinary_least_squares_linear_trend"
            fp.provenance = model_provenance
            points.append(fp)
        self._forecasts[key] = points
        return points

    def get_forecast_summary(self) -> Dict[str, Any]:
        forecasts = {}
        for key in ("30day", "90day", "1year"):
            pts = self._forecasts.get(key, [])
            if pts:
                forecasts[key] = {
                    "total_revenue": round(sum(p.predicted_revenue for p in pts), 2),
                    "total_profit": round(sum(p.predicted_profit for p in pts), 2),
                    "avg_daily": round(sum(p.predicted_revenue for p in pts) / len(pts), 2),
                    "avg_confidence": round(
                        sum(p.confidence for p in pts) / len(pts), 1
                    ),
                }
        return forecasts

    def forecast_roi(self, investment: float = 0.0) -> Dict[str, Any]:
        summary = self.get_forecast_summary()
        forecast_30 = summary.get("30day", {})
        predicted_30 = forecast_30.get("total_revenue", 0)
        if investment <= 0:
            raise ValueError("ROI forecast requires a real investment amount; no synthetic default is permitted")
        inv = float(investment)
        roi_30 = ((predicted_30 - inv) / inv * 100) if inv > 0 else 0
        predicted_90 = summary.get("90day", {}).get("total_revenue", 0)
        roi_90 = ((predicted_90 - inv * 3) / (inv * 3) * 100) if inv > 0 else 0
        predicted_1y = summary.get("1year", {}).get("total_revenue", 0)
        roi_1y = ((predicted_1y - inv * 12) / (inv * 12) * 100) if inv > 0 else 0
        self._roi_forecast = {
            "investment": round(inv, 2),
            "roi_30day": round(roi_30, 1),
            "roi_90day": round(roi_90, 1),
            "roi_1year": round(roi_1y, 1),
            "payback_days": round(inv / (predicted_30 / 30), 0) if predicted_30 > 0 else 0,
        }
        return self._roi_forecast

    def get_full_forecast(self) -> Dict[str, Any]:
        return {
            "historical_days": len(self._historical),
            "forecasts": self.get_forecast_summary(),
            "roi": dict(self._roi_forecast) if self._roi_forecast else {
                "available": False,
                "reason": "investment_required",
            },
            "30day_points": [p.to_dict() for p in self._forecasts.get("30day", [])[:7]],
            "90day_points": [p.to_dict() for p in self._forecasts.get("90day", [])[:7]],
        }

    def stats(self) -> Dict[str, Any]:
        return {
            "historical": len(self._historical),
            "forecasts": len(self._forecasts),
            "model": "ordinary_least_squares_linear_trend" if self._historical else None,
            "observations": len(self._historical),
            "confidence_scale": "0_to_100",
            "provenance_required": True,
        }


def get_revenue_forecasting() -> RevenueForecasting:
    return RevenueForecasting()
