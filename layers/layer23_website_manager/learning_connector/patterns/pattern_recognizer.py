"""PatternRecognizer — Identify patterns in performance data."""
from __future__ import annotations
import time
import threading
from typing import Any, Dict, List, Optional
from collections import Counter

from layers.layer23_website_manager.learning_connector.models.learning_models import (
    LearnedPattern, LearningEvent,
)


class PatternRecognizer:
    """Recognize patterns in learning data."""

    def __init__(self) -> None:
        self._patterns: Dict[str, LearnedPattern] = {}
        self._lock = threading.RLock()

    def recognize(self, pattern_name: str, description: str = "",
                  confidence: float = 0.5, source: str = "",
                  support_count: int = 1) -> LearnedPattern:
        with self._lock:
            existing = None
            for p in self._patterns.values():
                if p.pattern_name == pattern_name:
                    existing = p
                    break
            if existing:
                existing.support_count += 1
                existing.confidence = min(1.0, existing.confidence + 0.05)
                return existing
            pattern = LearnedPattern(pattern_name, description, confidence,
                                     source, support_count)
            self._patterns[pattern.pattern_id] = pattern
            return pattern

    def get_pattern(self, pattern_id: str) -> Optional[LearnedPattern]:
        return self._patterns.get(pattern_id)

    def get_patterns_by_source(self, source: str) -> List[LearnedPattern]:
        return [p for p in self._patterns.values() if p.source == source]

    def get_all_patterns(self) -> List[LearnedPattern]:
        return list(self._patterns.values())

    def analyze_events(self, events: List[LearningEvent]) -> List[LearnedPattern]:
        detected = []
        if not events:
            return detected

        # Detect high success rate pattern
        success_count = sum(1 for e in events if e.success)
        total = len(events)
        if total > 10:
            rate = success_count / total
            if rate > 0.9:
                p = self.recognize(
                    "high_success_rate",
                    f"Success rate: {rate:.0%}",
                    confidence=rate,
                    source="pattern_recognizer",
                    support_count=total,
                )
                detected.append(p)
            elif rate < 0.5:
                p = self.recognize(
                    "low_success_rate",
                    f"Success rate: {rate:.0%}",
                    confidence=1.0 - rate,
                    source="pattern_recognizer",
                    support_count=total,
                )
                detected.append(p)

        # Detect high scoring pattern
        high_scores = [e for e in events if e.score >= 0.8]
        if len(high_scores) >= 3:
            p = self.recognize(
                "high_performance",
                f"{len(high_scores)} events with score >= 0.8",
                confidence=0.7,
                source="pattern_recognizer",
            )
            detected.append(p)

        return detected

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "total_patterns": len(self._patterns),
                "avg_confidence": round(
                    sum(p.confidence for p in self._patterns.values()) /
                    max(len(self._patterns), 1), 2
                ),
                "active_patterns": sum(1 for p in self._patterns.values()
                                        if p.status == "active"),
            }
