"""StrategyLearner — Learn winning strategies from performance data."""
from __future__ import annotations
import time
import threading
from typing import Any, Dict, List, Optional
from collections import Counter

from layers.layer23_website_manager.learning_connector.models.learning_models import (
    PerformanceMetric, LearnedPattern,
)


class StrategyLearner:
    """Learn optimal strategies from performance patterns."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._learnings: Dict[str, Dict[str, Any]] = {}

    def learn(self, key: str, value: Any, source: str = "",
              confidence: float = 0.5) -> Dict[str, Any]:
        with self._lock:
            if key not in self._learnings:
                self._learnings[key] = {
                    "value": value,
                    "source": source,
                    "confidence": confidence,
                    "support_count": 1,
                    "first_learned": time.time(),
                    "last_updated": time.time(),
                }
            else:
                entry = self._learnings[key]
                entry["value"] = value
                entry["confidence"] = (entry["confidence"] + confidence) / 2
                entry["support_count"] += 1
                entry["last_updated"] = time.time()
            return self._learnings[key]

    def get_learning(self, key: str) -> Optional[Dict[str, Any]]:
        return self._learnings.get(key)

    def get_all_learnings(self) -> Dict[str, Dict[str, Any]]:
        with self._lock:
            return dict(self._learnings)

    def learn_from_metrics(self, metrics: List[PerformanceMetric]) -> List[str]:
        learned_keys = []
        best = {}
        for m in metrics:
            if m.target > 0:
                ratio = m.value / m.target
                if ratio >= 1.0:
                    key = f"best_{m.name}_{m.module}"
                    self.learn(key, {"name": m.name, "value": m.value,
                                      "target": m.target, "ratio": ratio},
                               source=f"analyzer/{m.module}", confidence=ratio * 0.5)
                    learned_keys.append(key)
        return learned_keys

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "total_learnings": len(self._learnings),
                "avg_confidence": round(
                    sum(e["confidence"] for e in self._learnings.values()) /
                    max(len(self._learnings), 1), 2
                ),
            }
