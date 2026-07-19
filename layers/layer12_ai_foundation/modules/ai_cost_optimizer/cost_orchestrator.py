"""CostOrchestrator — full cost management pipeline."""
from __future__ import annotations
from typing import Any, Dict, Optional
from .cost_tracker import CostTracker
from .budget_manager import BudgetManager
from .price_calculator import PriceCalculator
from .cost_optimizer import CostOptimizer
from .cost_memory import CostMemory
from .cost_analytics import CostAnalytics
from .cost_events import CostEvents
from .cost_health import CostHealth
from .cost_config import CostConfig
from .model_switcher import ModelSwitcher

class CostOrchestrator:
    def __init__(self, config: Optional[CostConfig] = None) -> None:
        self.config = config or CostConfig()
        self.tracker = CostTracker(self.config.daily_budget)
        self.budget = BudgetManager()
        self.optimizer = CostOptimizer()
        self.memory = CostMemory()
        self.analytics = CostAnalytics()
        self.events = CostEvents()
        self.health = CostHealth()
        self.switcher = ModelSwitcher()
        self._is_running = False
    def start(self) -> bool:
        self._is_running = True; self.events.publish("started"); return True
    def stop(self) -> bool:
        self._is_running = False; self.events.publish("stopped"); return True
    def record_cost(self, provider: str, model: str, prompt_tokens: int,
                    completion_tokens: int, cost: float) -> Dict[str, Any]:
        entry = self.tracker.record(provider, model, prompt_tokens, completion_tokens, cost)
        self.budget.record_spend(cost)
        self.memory.store(provider, model, cost)
        self.events.publish("cost_recorded", {"provider": provider, "cost": cost})
        if self.tracker.is_over_daily_budget():
            self.events.publish("budget_exceeded", {"total": self.tracker.today_total()})
        return entry.to_dict()
    def estimate_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        return PriceCalculator.calculate(model, prompt_tokens, completion_tokens)
    def find_best_model(self, prompt_tokens: int, completion_tokens: int,
                        quality: str = "medium") -> str:
        return self.optimizer.suggest_model(quality, self.budget.remaining_daily())
    def get_health(self) -> Dict[str, Any]:
        return self.health.overall_health()
    def get_stats(self) -> Dict[str, Any]:
        return {**self.tracker.to_dict(), "budget": self.budget.to_dict()}
