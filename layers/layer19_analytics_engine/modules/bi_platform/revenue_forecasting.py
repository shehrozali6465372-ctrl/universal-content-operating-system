"""RevenueForecasting — 30-day, 90-day, 1-year predictions + ROI forecast."""
from __future__ import annotations
import threading
import time
from typing import Any, Dict, List, Optional


class ForecastPoint:
    __slots__ = ("date", "predicted_revenue", "predicted_profit", "confidence",
                 "lower_bound", "upper_bound")

    def __init__(self, date: str, revenue: float = 0.0) -> None:
        self.date = date
        self.predicted_revenue = revenue
        self.predicted_profit = 0.0
        self.confidence = 50.0
        self.lower_bound = revenue * 0.6
        self.upper_bound = revenue * 1.4

    def to_dict(self) -> Dict[str, Any]:
        return {
            "date": self.date,
            "revenue": round(self.predicted_revenue, 2),
            "profit": round(self.predicted_profit, 2),
            "confidence": round(self.confidence, 1),
            "range": [round(self.lower_bound, 2), round(self.upper_bound, 2)],
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
        avg_revenue = 0.0
        growth_rate = 0.02
        if self._historical:
            revenues = [h["revenue"] for h in self._historical]
            avg_revenue = sum(revenues) / len(revenues) if revenues else 0
            if len(revenues) >= 2:
                recent_avg = sum(revenues[-7:]) / min(7, len(revenues))
                older_avg = sum(revenues[:7]) / min(7, len(revenues))
                if older_avg > 0:
                    growth_rate = max((recent_avg / older_avg - 1), 0.01)
        points = []
        base = avg_revenue if avg_revenue > 0 else 100.0
        confidence_base = min(len(self._historical) / 30, 1.0) * 70 + 20
        for i in range(1, days + 1):
            day = time.strftime("%Y-%m-%d", time.localtime(time.time() + i * 86400))
            predicted = base * ((1 + growth_rate) ** i)
            confidence = max(confidence_base - (i * 0.5), 20)
            fp = ForecastPoint(day, predicted)
            fp.predicted_profit = predicted * 0.7
            fp.confidence = confidence
            fp.lower_bound = predicted * (1 - (1 - confidence / 100))
            fp.upper_bound = predicted * (1 + (1 - confidence / 100))
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
        inv = investment if investment > 0 else max(predicted_30 * 0.3, 100)
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
            "roi": self.forecast_roi(),
            "30day_points": [p.to_dict() for p in self._forecasts.get("30day", [])[:7]],
            "90day_points": [p.to_dict() for p in self._forecasts.get("90day", [])[:7]],
        }

    def stats(self) -> Dict[str, Any]:
        return {
            "historical": len(self._historical),
            "forecasts": len(self._forecasts),
        }


def get_revenue_forecasting() -> RevenueForecasting:
    return RevenueForecasting()
