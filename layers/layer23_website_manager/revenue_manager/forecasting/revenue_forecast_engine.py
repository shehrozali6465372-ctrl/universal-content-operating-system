"""RevenueForecastEngine — Predict daily, weekly, monthly, yearly revenue."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from layers.layer23_website_manager.revenue_manager.models.revenue_models import RevenueForecast, RevenuePeriod


class RevenueForecastEngine:
    def forecast(self, historical_daily_avg: float, growth_rate: float = 0.05,
                  period: RevenuePeriod = RevenuePeriod.MONTHLY, seasonal_factor: float = 1.0) -> RevenueForecast:
        day_mult = {"daily": 1, "weekly": 7, "monthly": 30, "yearly": 365}
        days = day_mult.get(period.value, 30)
        predicted = historical_daily_avg * days * (1 + growth_rate) * seasonal_factor
        confidence = min(0.95, max(0.3, 0.85 - (days * 0.001)))
        return RevenueForecast(period=period, predicted_revenue=round(predicted, 2),
            predicted_commission=round(predicted * 0.06, 2), confidence=round(confidence, 2),
            low_estimate=round(predicted * 0.8, 2), high_estimate=round(predicted * 1.2, 2),
            factors=[f"Daily avg: ${historical_daily_avg:.2f}", f"Growth: {growth_rate*100:.0f}%"])

    def get_stats(self) -> Dict: return {"available": True}
