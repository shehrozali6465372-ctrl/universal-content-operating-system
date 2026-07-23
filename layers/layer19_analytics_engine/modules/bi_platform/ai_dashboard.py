"""AIDashboard — AI accuracy, quality, prompt performance, learning, memory, RAG."""
from __future__ import annotations
import threading
import time
from typing import Any, Dict, List, Optional


class AIMetricSnapshot:
    __slots__ = ("accuracy", "quality_score", "prompt_success_rate",
                 "learning_rate", "memory_usage_mb", "rag_accuracy",
                 "total_predictions", "correct_predictions",
                 "total_prompts_used", "knowledge_entries",
                 "timestamp")

    def __init__(self) -> None:
        self.accuracy = 0.0
        self.quality_score = 0.0
        self.prompt_success_rate = 0.0
        self.learning_rate = 0.0
        self.memory_usage_mb = 0.0
        self.rag_accuracy = 0.0
        self.total_predictions = 0
        self.correct_predictions = 0
        self.total_prompts_used = 0
        self.knowledge_entries = 0
        self.timestamp = time.time()

    @property
    def overall_health(self) -> float:
        return (self.accuracy * 0.25 + self.quality_score * 0.25 +
                self.prompt_success_rate * 0.2 + self.rag_accuracy * 0.2 +
                min(self.learning_rate / 10, 1.0) * 0.1) * 100

    def to_dict(self) -> Dict[str, Any]:
        return {
            "accuracy": round(self.accuracy * 100, 1),
            "quality": round(self.quality_score * 100, 1),
            "prompt_success": round(self.prompt_success_rate * 100, 1),
            "learning_rate": round(self.learning_rate, 1),
            "memory_mb": round(self.memory_usage_mb, 1),
            "rag_accuracy": round(self.rag_accuracy * 100, 1),
            "predictions": self.total_predictions,
            "correct": self.correct_predictions,
            "prompts_used": self.total_prompts_used,
            "knowledge": self.knowledge_entries,
            "overall_health": round(self.overall_health, 1),
        }


class AIDashboard:
    """Monitors AI system performance: accuracy, quality, prompts, learning, RAG."""
    _instance: Optional["AIDashboard"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "AIDashboard":
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
        self._current = AIMetricSnapshot()
        self._history: List[Dict[str, Any]] = []
        self._component_scores: Dict[str, float] = {}

    def update_metrics(self, accuracy: float = 0.0, quality: float = 0.0,
                       prompt_success: float = 0.0, learning_rate: float = 0.0,
                       memory_mb: float = 0.0, rag_accuracy: float = 0.0,
                       predictions: int = 0, correct: int = 0,
                       prompts_used: int = 0, knowledge: int = 0) -> AIMetricSnapshot:
        snap = AIMetricSnapshot()
        snap.accuracy = accuracy
        snap.quality_score = quality
        snap.prompt_success_rate = prompt_success
        snap.learning_rate = learning_rate
        snap.memory_usage_mb = memory_mb
        snap.rag_accuracy = rag_accuracy
        snap.total_predictions = predictions
        snap.correct_predictions = correct
        snap.total_prompts_used = prompts_used
        snap.knowledge_entries = knowledge
        self._current = snap
        self._history.append(snap.to_dict())
        if len(self._history) > 1000:
            self._history = self._history[-500:]
        return snap

    def update_component_score(self, component: str, score: float) -> None:
        self._component_scores[component] = score

    def get_current(self) -> AIMetricSnapshot:
        return self._current

    def get_trend(self, metric: str = "accuracy", limit: int = 30) -> List[float]:
        values = {
            "accuracy": [h.get("accuracy", 0) for h in self._history[-limit:]],
            "quality": [h.get("quality", 0) for h in self._history[-limit:]],
            "rag": [h.get("rag_accuracy", 0) for h in self._history[-limit:]],
        }
        return values.get(metric, [])

    def get_dashboard(self) -> Dict[str, Any]:
        current = self._current
        return {
            "current": current.to_dict(),
            "components": self._component_scores,
            "history_size": len(self._history),
            "trend_accuracy": self.get_trend("accuracy")[-7:],
            "trend_quality": self.get_trend("quality")[-7:],
        }

    def stats(self) -> Dict[str, Any]:
        return {
            "snapshots": len(self._history),
            "components": len(self._component_scores),
        }


def get_ai_dashboard() -> AIDashboard:
    return AIDashboard()
