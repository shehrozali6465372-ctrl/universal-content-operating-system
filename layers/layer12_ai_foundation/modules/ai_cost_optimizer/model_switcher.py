"""ModelSwitcher — switch models to optimize cost."""
from __future__ import annotations

from typing import Dict, List


class ModelSwitcher:
    TIERS: Dict[str, List[str]] = {
        "cheapest": ["gpt-5.6-luna", "gemini-3.8-flash", "deepseek-flash"],
        "balanced": ["gpt-5.6-luna", "gemini-3.8-flash", "deepseek-v4-pro"],
        "high_quality": ["gpt-5.6-sol", "deepseek-v4-pro", "gpt-5.6-luna"],
    }

    def __init__(self) -> None:
        self._switches: List[dict] = []

    def switch_down(self, current_model: str, budget_remaining: float) -> str:
        if budget_remaining < 0.001 and current_model not in self.TIERS["cheapest"]:
            return "gpt-5.6-luna"
        return current_model

    def switch_up(self, current_model: str, budget_remaining: float) -> str:
        if budget_remaining > 0.05 and current_model != "gpt-5.6-sol":
            return "gpt-5.6-sol"
        return current_model

    def suggest_tier(self, budget: float) -> str:
        if budget < 0.01:
            return "cheapest"
        if budget < 0.1:
            return "balanced"
        return "high_quality"

    def log_switch(self, from_model: str, to_model: str, reason: str) -> None:
        self._switches.append(
            {"from": from_model, "to": to_model, "reason": reason}
        )

    def get_switches(self) -> List[dict]:
        return list(self._switches)
