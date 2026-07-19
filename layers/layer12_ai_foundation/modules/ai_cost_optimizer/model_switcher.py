"""ModelSwitcher — switch models to optimize cost."""
from __future__ import annotations
from typing import Dict, List

class ModelSwitcher:
    TIERS: Dict[str, List[str]] = {
        "cheapest": ["gemini-2.0-flash", "gpt-4o-mini", "deepseek-chat"],
        "balanced": ["gpt-4o-mini", "claude-sonnet-4-20250514", "gpt-4o"],
        "high_quality": ["gpt-4o", "claude-sonnet-4-20250514", "gemini-2.0-flash"],
    }
    def __init__(self) -> None:
        self._switches: List[dict] = []
    def switch_down(self, current_model: str, budget_remaining: float) -> str:
        if budget_remaining < 0.001 and current_model not in self.TIERS["cheapest"]:
            return "gemini-2.0-flash"
        return current_model
    def switch_up(self, current_model: str, budget_remaining: float) -> str:
        if budget_remaining > 0.05 and current_model != "gpt-4o":
            return "gpt-4o"
        return current_model
    def suggest_tier(self, budget: float) -> str:
        if budget < 0.01: return "cheapest"
        elif budget < 0.1: return "balanced"
        return "high_quality"
    def log_switch(self, from_model: str, to_model: str, reason: str) -> None:
        self._switches.append({"from": from_model, "to": to_model, "reason": reason})
    def get_switches(self) -> List[dict]:
        return list(self._switches)
