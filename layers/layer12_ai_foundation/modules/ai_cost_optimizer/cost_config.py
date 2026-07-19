"""CostConfig — configuration for the cost optimizer."""
from __future__ import annotations
from typing import Any, Dict

class CostConfig:
    def __init__(self, **kwargs: Any) -> None:
        self.daily_budget: float = kwargs.get("daily_budget", 10.0)
        self.weekly_budget: float = kwargs.get("weekly_budget", 50.0)
        self.monthly_budget: float = kwargs.get("monthly_budget", 200.0)
        self.alert_threshold: float = kwargs.get("alert_threshold", 0.8)
        self.enable_forecasting: bool = kwargs.get("enable_forecasting", True)
        self.enable_optimization: bool = kwargs.get("enable_optimization", True)
        self.enable_switching: bool = kwargs.get("enable_switching", True)
        self.default_model: str = kwargs.get("default_model", "gpt-4o-mini")
        self.fallback_model: str = kwargs.get("fallback_model", "gemini-2.0-flash")
    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if not k.startswith("_")}
