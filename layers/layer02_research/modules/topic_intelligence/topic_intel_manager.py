"""
Topic Intelligence Manager
Layer 2: Research Engine — Module 2

Central manager for Facebook topic intelligence:
- Topic CRUD with scoring
- Auto-categorization
- Topic ranking and filtering
- Cluster management
- Persistent storage
- History and comparison
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Dict, List, Optional

from layers.layer02_research.modules.topic_intelligence.topic_entry import TopicEntry
from layers.layer02_research.modules.topic_intelligence.topic_scorer import TopicScorer
from layers.layer02_research.modules.topic_intelligence.topic_categorizer import TopicCategorizer
from layers.layer02_research.modules.topic_intelligence.exceptions import (
    TopicNotFoundError,
    DuplicateTopicError,
)


class TopicIntelManager:
    """Central Facebook topic intelligence engine."""

    def __init__(self, storage_path: Optional[str] = None):
        self._topics: Dict[str, TopicEntry] = {}
        self._lock = Lock()
        self._storage_path = Path(storage_path) if storage_path else None
        self._scorer = TopicScorer()
        self._categorizer = TopicCategorizer()
        self._history: List[dict] = []
        self._max_history = 500
        self._load()

    # ── CRUD ────────────────────────────────

    def add_topic(
        self,
        name: str,
        niche: str = "general",
        category: str = "general",
        engagement_score: float = 0.0,
        audience_fit_score: float = 0.0,
        competition_score: float = 0.0,
        estimated_reach: int = 0,
        difficulty_level: str = "medium",
        keywords: Optional[List[str]] = None,
        hashtags: Optional[List[str]] = None,
        related_topics: Optional[List[str]] = None,
        source_trend_id: str = "",
        confidence: float = 0.5,
        auto_categorize: bool = True,
    ) -> TopicEntry:
        """Add a new topic."""
        # Check duplicate name
        with self._lock:
            for t in self._topics.values():
                if t.name.lower() == name.lower():
                    raise DuplicateTopicError(f"Topic '{name}' already exists")

        topic = TopicEntry(
            name=name,
            niche=niche,
            category=category,
            engagement_score=engagement_score,
            audience_fit_score=audience_fit_score,
            competition_score=competition_score,
            estimated_reach=estimated_reach,
            difficulty_level=difficulty_level,
            keywords=keywords,
            hashtags=hashtags,
            related_topics=related_topics,
            source_trend_id=source_trend_id,
            confidence=confidence,
        )

        # Auto-categorize if enabled
        if auto_categorize and keywords:
            topic = self._categorizer.auto_categorize(topic)

        # Score the topic
        self._scorer.score_topic(topic)

        with self._lock:
            self._topics[topic.topic_id] = topic
            self._record_event("topic_added", topic.topic_id, {"name": name, "niche": topic.niche})
            self._save()

        return topic

    def get_topic(self, topic_id: str) -> TopicEntry:
        """Get a topic by ID."""
        with self._lock:
            topic = self._topics.get(topic_id)
        if topic is None:
            raise TopicNotFoundError(f"Topic '{topic_id}' not found")
        return topic

    def get_topic_by_name(self, name: str) -> Optional[TopicEntry]:
        """Get a topic by name."""
        with self._lock:
            for t in self._topics.values():
                if t.name.lower() == name.lower():
                    return t
        return None

    def update_topic(self, topic_id: str, **kwargs) -> TopicEntry:
        """Update topic fields."""
        with self._lock:
            topic = self._topics.get(topic_id)
            if topic is None:
                raise TopicNotFoundError(f"Topic '{topic_id}' not found")

            score_fields = {"engagement_score", "audience_fit_score", "competition_score"}
            score_updates = {k: v for k, v in kwargs.items() if k in score_fields}
            other_updates = {k: v for k, v in kwargs.items() if k not in score_fields}

            for key, val in other_updates.items():
                if hasattr(topic, key):
                    setattr(topic, key, val)

            if score_updates:
                topic.update_scores(**score_updates)
                self._scorer.score_topic(topic)

            topic.updated_at = datetime.now(timezone.utc).isoformat()
            self._record_event("topic_updated", topic_id, {"fields": list(kwargs.keys())})
            self._save()

        return topic

    def delete_topic(self, topic_id: str) -> bool:
        """Delete a topic."""
        with self._lock:
            if topic_id not in self._topics:
                raise TopicNotFoundError(f"Topic '{topic_id}' not found")
            del self._topics[topic_id]
            self._record_event("topic_deleted", topic_id, {})
            self._save()
        return True

    def exists(self, name: str) -> bool:
        """Check if a topic with this name exists."""
        with self._lock:
            return any(t.name.lower() == name.lower() for t in self._topics.values())

    def list_topics(self, niche: Optional[str] = None, status: Optional[str] = None) -> List[TopicEntry]:
        """List all topics with optional filters."""
        with self._lock:
            topics = list(self._topics.values())
        if niche:
            topics = [t for t in topics if t.niche == niche]
        if status:
            topics = [t for t in topics if t.status == status]
        return topics

    # ── Intelligence ────────────────────────

    def rank_topics(self, niche: Optional[str] = None) -> List[TopicEntry]:
        """Rank topics by composite score."""
        topics = self.list_topics(niche=niche)
        return self._scorer.rank_topics(topics)

    def get_top_topics(self, count: int = 10, niche: Optional[str] = None) -> List[TopicEntry]:
        """Get top N topics."""
        return self.rank_topics(niche=niche)[:count]

    def get_promotable_topics(self) -> List[TopicEntry]:
        """Get topics that are ready for promotion."""
        with self._lock:
            topics = list(self._topics.values())
        return [t for t in topics if t.is_promotable()]

    def find_opportunities(self, min_score: float = 7.0) -> List[TopicEntry]:
        """Find high-opportunity topics."""
        with self._lock:
            topics = list(self._topics.values())
        return [
            t for t in topics
            if t.opportunity_score >= min_score
            and not t.is_expired()
            and t.status == "active"
        ]

    def suggest_for_niche(self, niche: str, count: int = 5) -> List[TopicEntry]:
        """Suggest best topics for a specific niche."""
        topics = self.list_topics(niche=niche, status="active")
        scored = self._scorer.rank_topics(topics)
        return scored[:count]

    def cluster_topics(self) -> Dict[str, List[str]]:
        """Cluster all topics."""
        with self._lock:
            topics = list(self._topics.values())
        return self._categorizer.cluster_topics(topics)

    def get_niche_stats(self) -> Dict[str, Dict]:
        """Get statistics per niche."""
        with self._lock:
            topics = list(self._topics.values())
        return self._categorizer.get_niche_stats(topics)

    def cleanup_expired(self) -> int:
        """Remove expired topics."""
        removed = 0
        with self._lock:
            expired_ids = [
                tid for tid, t in self._topics.items()
                if t.is_expired()
            ]
            for tid in expired_ids:
                self._topics[tid].status = "expired"
                removed += 1
            if removed:
                self._save()
        return removed

    def health_check(self) -> dict:
        """System health check."""
        with self._lock:
            topics = list(self._topics.values())
        active = sum(1 for t in topics if t.status == "active")
        expired = sum(1 for t in topics if t.is_expired())
        niches = set(t.niche for t in topics)
        avg_score = (
            round(sum(t.composite_score for t in topics) / len(topics), 2)
            if topics else 0.0
        )
        return {
            "total_topics": len(topics),
            "active": active,
            "expired": expired,
            "niches_covered": len(niches),
            "avg_composite_score": avg_score,
            "scorer_ready": True,
            "categorizer_ready": True,
        }

    # ── Storage ─────────────────────────────

    def _record_event(self, event_type: str, topic_id: str, data: dict):
        entry = {
            "event": event_type,
            "topic_id": topic_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **data,
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
            "topics": [t.to_dict() for t in self._topics.values()],
            "history": self._history[-50:],
        }
        self._storage_path.write_text(json.dumps(data, indent=2))

    def _load(self):
        if self._storage_path is None or not self._storage_path.exists():
            return
        try:
            data = json.loads(self._storage_path.read_text())
            for td in data.get("topics", []):
                topic = TopicEntry.from_dict(td)
                self._topics[topic.topic_id] = topic
            self._history = data.get("history", [])
        except (json.JSONDecodeError, KeyError):
            pass
