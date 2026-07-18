"""DynamicPrompt — adapt prompts based on context, history, and feedback."""
from __future__ import annotations

import time
from typing import Any, Dict, List


class DynamicPrompt:
    """Adapt prompts based on context, history, and feedback."""

    def __init__(self) -> None:
        self._context: Dict[str, Any] = {}
        self._feedback_history: List[Dict[str, Any]] = []
        self._adaptation_rules: List[Dict[str, Any]] = []

    def set_context(self, key: str, value: Any) -> None:
        self._context[key] = value

    def get_context(self, key: str, default: Any = None) -> Any:
        return self._context.get(key, default)

    def add_feedback(self, prompt: str, outcome: str, score: float) -> None:
        self._feedback_history.append({
            "prompt_hash": hash(prompt) % 10**8,
            "outcome": outcome, "score": score,
            "timestamp": time.time(),
        })

    def add_rule(self, condition: str, modification: str) -> None:
        self._adaptation_rules.append({"condition": condition,
                                       "modification": modification})

    def adapt(self, base_prompt: str) -> str:
        adapted = base_prompt
        for rule in self._adaptation_rules:
            if self._evaluate_condition(rule["condition"]):
                adapted += f"\n{rule['modification']}"
        return adapted

    def _evaluate_condition(self, condition: str) -> bool:
        if condition.startswith("context:"):
            key = condition.split(":", 1)[1]
            return key in self._context
        if condition.startswith("feedback_avg>"):
            threshold = float(condition.split(">")[1])
            if self._feedback_history:
                avg = sum(f["score"] for f in self._feedback_history) / len(self._feedback_history)
                return avg > threshold
        return False

    def get_recent_feedback(self, limit: int = 5) -> List[Dict[str, Any]]:
        return self._feedback_history[-limit:]

    def clear(self) -> None:
        self._context.clear()
        self._feedback_history.clear()
        self._adaptation_rules.clear()
