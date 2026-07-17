"""ResourcePlanner — Plan resource allocation for execution."""
from __future__ import annotations
from typing import Any, Dict, List


class ResourcePlan:
    """Planned resource allocation."""

    __slots__ = ("plan_id", "cpu_cores", "memory_gb", "gpu_count",
                 "api_calls", "budget", "time_estimate_seconds")

    def __init__(self) -> None:
        self.plan_id: str = ""
        self.cpu_cores: float = 2.0
        self.memory_gb: float = 4.0
        self.gpu_count: int = 0
        self.api_calls: int = 100
        self.budget: float = 10.0
        self.time_estimate_seconds: float = 60.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cpu_cores": self.cpu_cores, "memory_gb": self.memory_gb,
            "gpu_count": self.gpu_count, "api_calls": self.api_calls,
            "budget": self.budget, "time_estimate_seconds": self.time_estimate_seconds,
        }


class ResourcePlanner:
    """Plan and estimate resources for execution plans."""

    LAYER_COSTS = {
        "layer01_core": {"cpu": 0.5, "memory": 1, "api": 0, "time": 5},
        "layer02_research": {"cpu": 1, "memory": 2, "api": 10, "time": 30},
        "layer03_intelligence": {"cpu": 2, "memory": 4, "api": 5, "time": 20},
        "layer04_writing": {"cpu": 1, "memory": 2, "api": 20, "time": 15},
        "layer05_image": {"cpu": 2, "memory": 4, "gpu": 1, "api": 5, "time": 30},
        "layer06_quality": {"cpu": 1, "memory": 2, "api": 10, "time": 10},
        "layer07_publishing": {"cpu": 0.5, "memory": 1, "api": 5, "time": 10},
        "layer08_analytics": {"cpu": 1, "memory": 2, "api": 15, "time": 20},
        "layer09_learning": {"cpu": 2, "memory": 4, "api": 10, "time": 30},
    }

    def __init__(self, budget_limit: float = 100.0) -> None:
        self._budget_limit = budget_limit
        self._plans: List[ResourcePlan] = []

    def plan_for_layers(self, layers: List[str]) -> ResourcePlan:
        plan = ResourcePlan()
        for layer in layers:
            costs = self.LAYER_COSTS.get(layer, {})
            plan.cpu_cores = max(plan.cpu_cores, costs.get("cpu", 0.5))
            plan.memory_gb += costs.get("memory", 1)
            plan.gpu_count = max(plan.gpu_count, costs.get("gpu", 0))
            plan.api_calls += costs.get("api", 0)
            plan.time_estimate_seconds += costs.get("time", 10)

        plan.budget = plan.api_calls * 0.01 + plan.time_estimate_seconds * 0.001
        plan.budget = min(plan.budget, self._budget_limit)
        self._plans.append(plan)
        return plan

    def estimate_cost(self, layers: List[str]) -> float:
        total = 0.0
        for layer in layers:
            costs = self.LAYER_COSTS.get(layer, {})
            total += costs.get("api", 0) * 0.01 + costs.get("time", 10) * 0.001
        return round(total, 4)

    def check_budget(self, plan: ResourcePlan) -> bool:
        return plan.budget <= self._budget_limit

    def get_stats(self) -> Dict[str, Any]:
        return {"total_plans": len(self._plans), "budget_limit": self._budget_limit}
