"""persistence_ai.py — AI-driven persistence optimization."""
from __future__ import annotations
from typing import Any, Dict, List


class PersistenceAI:
    """Uses AI to optimize persistence."""

    def __init__(self) -> None:
        self._insights: List[Dict[str, Any]] = []
        self._predictions: List[Dict[str, Any]] = []

    def analyze_patterns(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        insight = {"patterns": [], "confidence": 0.0}
        if metrics.get("write_heavy", False):
            insight["patterns"].append("write_heavy")
        if metrics.get("read_heavy", False):
            insight["patterns"].append("read_heavy")
        insight["confidence"] = min(1.0, len(insight["patterns"]) * 0.3)
        self._insights.append(insight)
        return insight

    def predict_growth(self, current: int, history: List[int]) -> Dict[str, Any]:
        if len(history) < 2:
            prediction = {"growth_rate": 0.0, "predicted_next": current}
        else:
            rates = [(history[i] - history[i - 1]) / max(1, history[i - 1])
                      for i in range(1, len(history))]
            avg_rate = sum(rates) / len(rates)
            predicted = int(current * (1 + avg_rate))
            prediction = {"growth_rate": avg_rate, "predicted_next": predicted}
        self._predictions.append(prediction)
        return prediction

    def get_insights(self) -> List[Dict[str, Any]]:
        return list(self._insights)

    def get_predictions(self) -> List[Dict[str, Any]]:
        return list(self._predictions)

    def stats(self) -> Dict[str, Any]:
        return {"insights": len(self._insights), "predictions": len(self._predictions)}
