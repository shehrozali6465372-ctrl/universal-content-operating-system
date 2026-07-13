"""
Scoring Manager
Layer 2: Research Engine — Module 8

Central manager for topic scoring:
- Score topics
- Batch scoring
- Comparison
- History tracking
- Persistent storage
- Health check
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Dict, List, Optional

from layers.layer02_research.modules.topic_scoring.scoring_engine import ScoringEngine, ScoringResult


class ScoringManager:
    """Central topic scoring manager."""

    def __init__(self, storage_path: Optional[str] = None):
        self._results: Dict[str, ScoringResult] = {}
        self._lock = Lock()
        self._storage_path = Path(storage_path) if storage_path else None

        self.engine = ScoringEngine()
        self.weight_manager = self.engine.weight_manager
        self.rules_engine = self.engine.rules_engine

        self._history: List[dict] = []
        self._max_history = 500

        self._load()

    def score_topic(
        self,
        topic: str,
        niche: str = "general",
        scores: Optional[Dict[str, float]] = None,
        evidence: Optional[List[str]] = None,
    ) -> ScoringResult:
        """Score a single topic."""
        result = self.engine.score(topic, niche, scores, evidence)

        with self._lock:
            self._results[topic] = result
            self._record_event("topic_scored", topic, {
                "overall_score": result.overall_score,
                "recommendation": result.recommendation,
                "confidence": result.confidence,
            })
            self._save()

        return result

    def score_batch(
        self,
        topics: List[Dict],
        niche: str = "general",
    ) -> List[ScoringResult]:
        """Score multiple topics."""
        results = []
        for topic_data in topics:
            topic = topic_data.get("topic", "")
            scores = topic_data.get("scores", {})
            evidence = topic_data.get("evidence", [])
            result = self.score_topic(topic, niche, scores, evidence)
            results.append(result)
        return results

    def get_result(self, topic: str) -> Optional[ScoringResult]:
        return self._results.get(topic)

    def get_ranked(self, count: int = 20) -> List[ScoringResult]:
        """Get topics ranked by overall score."""
        return sorted(self._results.values(), key=lambda r: r.overall_score, reverse=True)[:count]

    def get_recommendations(self, recommendation: str = "publish") -> List[ScoringResult]:
        """Get topics with a specific recommendation."""
        return [r for r in self._results.values() if r.recommendation == recommendation]

    def compare_topics(self, topic_a: str, topic_b: str) -> Dict:
        """Compare two scored topics."""
        a = self._results.get(topic_a)
        b = self._results.get(topic_b)
        if not a or not b:
            return {"error": "One or both topics not found"}
        return {
            "topic_a": topic_a, "topic_b": topic_b,
            "score_diff": round(a.overall_score - b.overall_score, 2),
            "a_score": a.overall_score, "b_score": b.overall_score,
            "a_recommendation": a.recommendation,
            "b_recommendation": b.recommendation,
            "winner": topic_a if a.overall_score > b.overall_score else topic_b,
        }

    def get_statistics(self) -> Dict:
        """Get scoring statistics."""
        if not self._results:
            return {"total": 0}
        scores = [r.overall_score for r in self._results.values()]
        recs = {}
        for r in self._results.values():
            recs[r.recommendation] = recs.get(r.recommendation, 0) + 1
        return {
            "total": len(self._results),
            "avg_score": round(sum(scores) / len(scores), 2),
            "max_score": round(max(scores), 2),
            "min_score": round(min(scores), 2),
            "recommendations": recs,
        }

    def health_check(self) -> dict:
        stats = self.get_statistics()
        return {
            "total_scored": stats.get("total", 0),
            "avg_score": stats.get("avg_score", 0),
            "available_niches": len(self.weight_manager.get_all_niches()),
            "active_rules": len(self.rules_engine.list_rules()),
            "engine_ready": True,
        }

    # ── Storage ─────────────────────────────

    def _record_event(self, event_type: str, topic: str, data: dict):
        entry = {
            "event": event_type, "topic": topic,
            "timestamp": datetime.now(timezone.utc).isoformat(), **data,
        }
        self._history.append(entry)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]

    def _save(self):
        if self._storage_path is None:
            return
        self._storage_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "version": 1,
            "saved_at": datetime.now(timezone.utc).isoformat(),
            "results": {t: r.to_dict() for t, r in self._results.items()},
            "history": self._history[-50:],
        }
        self._storage_path.write_text(json.dumps(data, indent=2))

    def _load(self):
        if self._storage_path is None or not self._storage_path.exists():
            return
        try:
            data = json.loads(self._storage_path.read_text())
            self._history = data.get("history", [])
        except (json.JSONDecodeError, KeyError):
            pass
