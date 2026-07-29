"""RecommendationEngine — Generate actionable recommendations."""
from __future__ import annotations
import time
import threading
from typing import Any, Dict, List, Optional

from layers.layer23_website_manager.learning_connector.models.learning_models import (
    Recommendation, MistakeRecord, LearnedPattern,
)


class RecommendationEngine:
    """Generate recommendations based on analysis."""

    def __init__(self) -> None:
        self._recommendations: Dict[str, Recommendation] = {}
        self._lock = threading.RLock()

    def add_recommendation(self, title: str, description: str = "",
                           category: str = "general", priority: str = "medium",
                           expected_impact: str = "low") -> Recommendation:
        rec = Recommendation(title, description, category, priority, expected_impact)
        with self._lock:
            self._recommendations[rec.recommendation_id] = rec
        return rec

    def get_recommendation(self, rec_id: str) -> Optional[Recommendation]:
        return self._recommendations.get(rec_id)

    def get_pending(self) -> List[Recommendation]:
        return [r for r in self._recommendations.values() if r.status == "pending"]

    def get_by_category(self, category: str) -> List[Recommendation]:
        return [r for r in self._recommendations.values() if r.category == category]

    def mark_implemented(self, rec_id: str) -> bool:
        with self._lock:
            rec = self._recommendations.get(rec_id)
            if not rec:
                return False
            rec.status = "implemented"
            rec.implemented_at = time.time()
            return True

    def dismiss(self, rec_id: str) -> bool:
        with self._lock:
            rec = self._recommendations.get(rec_id)
            if not rec:
                return False
            rec.status = "dismissed"
            return True

    def generate_from_mistakes(self, mistakes: List[MistakeRecord]) -> List[Recommendation]:
        generated = []
        for m in mistakes:
            if m.resolved:
                continue
            title = f"Fix {m.mistake_type} in {m.module}"
            desc = m.description or f"Address {m.severity} issue in {m.module}"
            rec = self.add_recommendation(
                title=title, description=desc,
                category="fix", priority=m.severity,
                expected_impact="medium",
            )
            generated.append(rec)
        return generated

    def generate_from_patterns(self,
                                patterns: List[LearnedPattern]) -> List[Recommendation]:
        generated = []
        for p in patterns:
            if "low" in p.pattern_name:
                rec = self.add_recommendation(
                    title=f"Address {p.pattern_name}",
                    description=p.description,
                    category="improvement",
                    priority="high",
                    expected_impact="high",
                )
                generated.append(rec)
        return generated

    def get_all_recommendations(self) -> List[Recommendation]:
        return list(self._recommendations.values())

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            all_recs = self._recommendations.values()
            return {
                "total": len(all_recs),
                "pending": sum(1 for r in all_recs if r.status == "pending"),
                "implemented": sum(1 for r in all_recs if r.status == "implemented"),
                "dismissed": sum(1 for r in all_recs if r.status == "dismissed"),
                "by_priority": {
                    p: sum(1 for r in all_recs if r.priority == p)
                    for p in {"low", "medium", "high", "critical"}
                },
            }
