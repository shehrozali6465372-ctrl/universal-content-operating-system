"""
Audience Intelligence Manager
Layer 2: Research Engine — Module 4

Central manager for audience intelligence:
- Audience segment CRUD
- Interest mapping
- Behavioral analysis
- Demographic profiling
- Engagement prediction
- Persistent storage
- Health check
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Dict, List, Optional

from layers.layer02_research.modules.audience_research.audience_profile import AudienceProfile
from layers.layer02_research.modules.audience_research.interest_mapper import InterestMapper
from layers.layer02_research.modules.audience_research.behavior_analyzer import BehaviorAnalyzer
from layers.layer02_research.modules.audience_research.demographic_analyzer import DemographicAnalyzer
from layers.layer02_research.modules.audience_research.engagement_predictor import EngagementPredictor, Prediction
from layers.layer02_research.modules.audience_research.exceptions import (
    AudienceNotFoundError, DuplicateAudienceError,
)


class AudienceIntelManager:
    """Central audience intelligence engine."""

    def __init__(self, storage_path: Optional[str] = None):
        self._audiences: Dict[str, AudienceProfile] = {}
        self._lock = Lock()
        self._storage_path = Path(storage_path) if storage_path else None

        # Sub-analyzers
        self.interest_mapper = InterestMapper()
        self.behavior_analyzer = BehaviorAnalyzer()
        self.demographic_analyzer = DemographicAnalyzer()
        self.engagement_predictor = EngagementPredictor()

        self._history: List[dict] = []
        self._max_history = 500

        self._load()

    # ── CRUD ────────────────────────────────

    def add_audience(
        self,
        segment_name: str,
        niche: str = "general",
        category: str = "general",
        age_range: Optional[List[int]] = None,
        gender_split: Optional[Dict[str, float]] = None,
        locations: Optional[List[str]] = None,
        languages: Optional[List[str]] = None,
        interests: Optional[List[str]] = None,
        behaviors: Optional[List[str]] = None,
        engagement_rate: float = 0.0,
        size_estimate: int = 0,
        confidence: float = 0.5,
        tags: Optional[List[str]] = None,
    ) -> AudienceProfile:
        """Add a new audience segment."""
        with self._lock:
            for aud in self._audiences.values():
                if aud.segment_name.lower() == segment_name.lower():
                    raise DuplicateAudienceError(f"Audience '{segment_name}' already exists")

        profile = AudienceProfile(
            segment_name=segment_name, niche=niche, category=category,
            age_range=age_range, gender_split=gender_split,
            locations=locations, languages=languages,
            interests=interests or [], behaviors=behaviors or [],
            engagement_rate=engagement_rate, size_estimate=size_estimate,
            confidence=confidence, tags=tags,
        )

        with self._lock:
            self._audiences[profile.profile_id] = profile
            self._record_event("audience_added", profile.profile_id, {"name": segment_name})
            self._save()

        # Auto-map interests
        for interest in interests or []:
            self.interest_mapper.add_interest(interest)

        return profile

    def get_audience(self, profile_id: str) -> AudienceProfile:
        with self._lock:
            aud = self._audiences.get(profile_id)
        if aud is None:
            raise AudienceNotFoundError(f"Audience '{profile_id}' not found")
        return aud

    def get_by_name(self, name: str) -> Optional[AudienceProfile]:
        with self._lock:
            for aud in self._audiences.values():
                if aud.segment_name.lower() == name.lower():
                    return aud
        return None

    def update_audience(self, profile_id: str, **kwargs) -> AudienceProfile:
        with self._lock:
            aud = self._audiences.get(profile_id)
            if aud is None:
                raise AudienceNotFoundError(f"Audience '{profile_id}' not found")
            for key, val in kwargs.items():
                if hasattr(aud, key):
                    setattr(aud, key, val)
            aud.updated_at = datetime.now(timezone.utc).isoformat()
            self._record_event("audience_updated", profile_id, {"fields": list(kwargs.keys())})
            self._save()
        return aud

    def delete_audience(self, profile_id: str) -> bool:
        with self._lock:
            if profile_id not in self._audiences:
                raise AudienceNotFoundError(f"Audience '{profile_id}' not found")
            del self._audiences[profile_id]
            self._record_event("audience_deleted", profile_id, {})
            self._save()
        return True

    def list_audiences(self, niche: Optional[str] = None, status: Optional[str] = None) -> List[AudienceProfile]:
        with self._lock:
            auds = list(self._audiences.values())
        if niche:
            auds = [a for a in auds if a.niche == niche]
        if status:
            auds = [a for a in auds if a.status == status]
        return auds

    def exists(self, name: str) -> bool:
        with self._lock:
            return any(a.segment_name.lower() == name.lower() for a in self._audiences.values())

    # ── Intelligence ────────────────────────

    def run_full_analysis(
        self,
        profile_id: str,
        interaction_hours: Optional[List[int]] = None,
        interaction_days: Optional[List[str]] = None,
        interaction_types: Optional[List[str]] = None,
        ages: Optional[List[int]] = None,
        genders: Optional[List[str]] = None,
        locations: Optional[List[str]] = None,
        languages: Optional[List[str]] = None,
        devices: Optional[List[str]] = None,
    ) -> AudienceProfile:
        """Run full analysis pipeline on an audience segment."""
        aud = self.get_audience(profile_id)

        # Interest mapping
        for interest in aud.interests:
            self.interest_mapper.add_interest(interest)

        # Behavioral analysis
        if interaction_hours and interaction_days:
            self.behavior_analyzer.analyze(
                profile_id,
                interaction_hours=interaction_hours,
                interaction_days=interaction_days,
                interaction_types=interaction_types,
            )
            behavior = self.behavior_analyzer.get_analysis(profile_id)
            if behavior:
                aud.peak_engagement_hours = behavior.online_peak_hours
                aud.online_hours = behavior.online_peak_hours

        # Demographic analysis
        if any([ages, genders, locations, languages, devices]):
            self.demographic_analyzer.analyze(
                profile_id, ages=ages, genders=genders,
                locations=locations, languages=languages, devices=devices,
            )

        aud.last_analyzed = datetime.now(timezone.utc).isoformat()
        aud.updated_at = aud.last_analyzed

        with self._lock:
            self._save()

        return aud

    def predict_engagement(
        self,
        profile_id: str,
        content_type: str = "text",
        topic: str = "general",
        posting_hour: int = 12,
    ) -> Prediction:
        """Predict engagement for content targeting this audience."""
        aud = self.get_audience(profile_id)
        return self.engagement_predictor.predict(
            aud, content_type=content_type, topic=topic, posting_hour=posting_hour,
        )

    def find_similar(self, profile_id: str) -> List[str]:
        """Find audiences with similar interests."""
        target = self.get_audiences(profile_id)
        if not target:
            return []

        similar = []
        for aud_id, aud in self._audiences.items():
            if aud_id == profile_id:
                continue
            overlap = self.interest_mapper.compute_overlap(target.interests, aud.interests)
            if overlap >= 0.3:
                similar.append((aud_id, overlap))

        similar.sort(key=lambda x: x[1], reverse=True)
        return [sid for sid, _ in similar[:5]]

    def get_content_recommendations(self, profile_id: str) -> Dict:
        """Get full content recommendations for an audience."""
        aud = self.get_audience(profile_id)
        behavior = self.behavior_analyzer.get_analysis(profile_id)

        best_hour = None
        best_day = None
        if behavior:
            best_hour = behavior.best_posting_hours[0] if behavior.best_posting_hours else None
            best_day = behavior.most_active_day

        # Interest-based suggestions
        suggestions = self.interest_mapper.suggest_content_topics(aud.interests, count=10)

        return {
            "audience": aud.segment_name,
            "best_posting_hour": best_hour,
            "best_posting_day": best_day,
            "suggested_topics": suggestions,
            "preferred_formats": aud.format_preferences,
            "content_preferences": aud.content_preferences,
            "engagement_rate": aud.engagement_rate,
            "size_tier": aud.get_size_tier(),
            "mobile_first": aud.get_mobile_percentage() > 50,
        }

    def health_check(self) -> dict:
        with self._lock:
            auds = list(self._audiences.values())
        active = sum(1 for a in auds if a.status == "active")
        high_value = sum(1 for a in auds if a.is_high_value())
        interests = len(self.interest_mapper.list_interests())
        return {
            "total_audiences": len(auds),
            "active": active,
            "high_value": high_value,
            "interests_mapped": interests,
            "interest_mapper_ready": True,
            "behavior_analyzer_ready": True,
            "demographic_analyzer_ready": True,
            "engagement_predictor_ready": True,
        }

    # ── Storage ─────────────────────────────

    def _record_event(self, event_type: str, aud_id: str, data: dict):
        entry = {
            "event": event_type, "audience_id": aud_id,
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
            "audiences": [a.to_dict() for a in self._audiences.values()],
            "history": self._history[-50:],
        }
        self._storage_path.write_text(json.dumps(data, indent=2))

    def _load(self):
        if self._storage_path is None or not self._storage_path.exists():
            return
        try:
            data = json.loads(self._storage_path.read_text())
            for ad in data.get("audiences", []):
                aud = AudienceProfile.from_dict(ad)
                self._audiences[aud.profile_id] = aud
            self._history = data.get("history", [])
        except (json.JSONDecodeError, KeyError):
            pass
