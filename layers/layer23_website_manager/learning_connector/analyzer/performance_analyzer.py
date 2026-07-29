"""PerformanceAnalyzer — Analyze module performance and identify trends."""
from __future__ import annotations
import time
import threading
from typing import Any, Dict, List, Optional
from collections import Counter

from layers.layer23_website_manager.learning_connector.models.learning_models import (
    PerformanceMetric, LearningEvent,
)


class PerformanceAnalyzer:
    """Analyze performance data to find best and worst performers."""

    def __init__(self) -> None:
        self._metrics: List[PerformanceMetric] = []
        self._lock = threading.RLock()

    def record_metric(self, name: str, module: str, value: float,
                      target: float = 0.0, trend: str = "stable") -> PerformanceMetric:
        metric = PerformanceMetric(name, module, value, target, trend)
        with self._lock:
            self._metrics.append(metric)
        return metric

    def get_metrics(self, module: Optional[str] = None,
                    name: Optional[str] = None) -> List[PerformanceMetric]:
        with self._lock:
            metrics = self._metrics
            if module:
                metrics = [m for m in metrics if m.module == module]
            if name:
                metrics = [m for m in metrics if m.name == name]
            return metrics

    def get_best_performers(self, module: str, top_k: int = 5) -> List[Dict[str, Any]]:
        metrics = self.get_metrics(module=module)
        scored = [(m.value / max(m.target, 1), m) for m in metrics if m.target > 0]
        scored.sort(key=lambda x: x[0], reverse=True)
        return [{"name": m.name, "value": m.value, "target": m.target,
                  "ratio": round(r, 2)} for r, m in scored[:top_k]]

    def get_worst_performers(self, module: str, top_k: int = 5) -> List[Dict[str, Any]]:
        metrics = self.get_metrics(module=module)
        scored = [(m.value / max(m.target, 1), m) for m in metrics if m.target > 0]
        scored.sort(key=lambda x: x[0])
        return [{"name": m.name, "value": m.value, "target": m.target,
                  "ratio": round(r, 2)} for r, m in scored[:top_k]]

    def analyze_events(self, events: List[LearningEvent]) -> Dict[str, Any]:
        if not events:
            return {"total": 0, "avg_score": 0.0}

        scores = [e.score for e in events if e.score > 0]
        types = Counter(e.event_type for e in events)
        modules = Counter(e.module for e in events)

        return {
            "total": len(events),
            "avg_score": round(sum(scores) / max(len(scores), 1), 2) if scores else 0.0,
            "success_rate": round(
                (sum(1 for e in events if e.success) / len(events)) * 100, 1
            ),
            "top_event_types": types.most_common(5),
            "top_modules": modules.most_common(5),
        }

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "total_metrics": len(self._metrics),
                "modules_tracked": len(set(m.module for m in self._metrics)),
                "metric_types": len(set(m.name for m in self._metrics)),
            }
