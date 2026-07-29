"""DecisionEngine — Make AI-driven decisions based on learning data."""
from __future__ import annotations
import time
import threading
from typing import Any, Dict, List, Optional

from layers.layer23_website_manager.learning_connector.models.learning_models import DecisionResult


class DecisionEngine:
    """Make decisions about automation strategy."""

    def __init__(self) -> None:
        self._decisions: List[DecisionResult] = []
        self._lock = threading.RLock()
        self._rules: Dict[str, Dict[str, Any]] = {}

    def add_decision_rule(self, question_pattern: str,
                          default_decision: str,
                          confidence: float = 0.5,
                          reasoning: str = "") -> None:
        with self._lock:
            self._rules[question_pattern] = {
                "decision": default_decision,
                "confidence": confidence,
                "reasoning": reasoning,
            }

    def decide(self, question: str,
               context: Optional[Dict[str, Any]] = None) -> DecisionResult:
        ctx = context or {}
        decision = "no_action"
        confidence = 0.5
        reasoning = "No matching rule found"

        with self._lock:
            for pattern, rule in self._rules.items():
                if pattern.lower() in question.lower():
                    decision = rule["decision"]
                    confidence = rule["confidence"]
                    reasoning = rule["reasoning"]
                    break

        # Adjust confidence based on context
        if ctx.get("success_rate", 1.0) < 0.5:
            confidence *= 0.8

        result = DecisionResult(question, decision, confidence, reasoning, ctx)
        with self._lock:
            self._decisions.append(result)
        return result

    def get_decisions(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._lock:
            return [d.to_dict() for d in self._decisions[-limit:]]

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "total_decisions": len(self._decisions),
                "rules_available": len(self._rules),
            }
