"""
Behavior Analyzer
Layer 2: Research Engine — Module 4

Analyzes audience behavioral patterns:
- Online activity patterns
- Content interaction patterns
- Sharing and saving behavior
- Time-of-day preferences
- Day-of-week patterns
- Device usage patterns
- Buying/signup triggers
"""

from collections import Counter
from typing import Dict, List, Optional, Tuple


class BehaviorAnalysis:
    """Result of behavioral analysis for an audience segment."""

    __slots__ = (
        "profile_id", "online_peak_hours", "engagement_peak_days",
        "top_interaction_types", "avg_interactions_per_session",
        "sharing_rate", "saving_rate", "click_rate",
        "active_device_preference", "best_posting_hours",
        "response_time_avg", "drop_off_rate",
        "most_active_day", "least_active_day",
        "behavior_consistency", "confidence",
    )

    def __init__(self, profile_id: str):
        self.profile_id = profile_id
        self.online_peak_hours: List[int] = []
        self.engagement_peak_days: List[str] = []
        self.top_interaction_types: List[Tuple[str, int]] = []
        self.avg_interactions_per_session = 0.0
        self.sharing_rate = 0.0
        self.saving_rate = 0.0
        self.click_rate = 0.0
        self.active_device_preference = "mobile"
        self.best_posting_hours: List[int] = []
        self.response_time_avg = 0.0  # hours
        self.drop_off_rate = 0.0
        self.most_active_day = ""
        self.least_active_day = ""
        self.behavior_consistency = 0.0
        self.confidence = 0.5

    def to_dict(self) -> dict:
        return {
            "profile_id": self.profile_id,
            "online_peak_hours": self.online_peak_hours,
            "engagement_peak_days": self.engagement_peak_days,
            "top_interaction_types": self.top_interaction_types,
            "avg_interactions_per_session": self.avg_interactions_per_session,
            "sharing_rate": self.sharing_rate,
            "saving_rate": self.saving_rate,
            "click_rate": self.click_rate,
            "active_device_preference": self.active_device_preference,
            "best_posting_hours": self.best_posting_hours,
            "response_time_avg": self.response_time_avg,
            "drop_off_rate": self.drop_off_rate,
            "most_active_day": self.most_active_day,
            "least_active_day": self.least_active_day,
            "behavior_consistency": self.behavior_consistency,
            "confidence": self.confidence,
        }


class BehaviorAnalyzer:
    """Analyze audience behavioral patterns."""

    DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    def __init__(self):
        self._analyses: Dict[str, BehaviorAnalysis] = {}

    def analyze(
        self,
        profile_id: str,
        interaction_hours: List[int],
        interaction_days: List[str],
        interaction_types: Optional[List[str]] = None,
        session_interactions: Optional[List[int]] = None,
    ) -> BehaviorAnalysis:
        """Full behavioral analysis."""
        analysis = BehaviorAnalysis(profile_id)

        # Peak hours
        hour_counter = Counter(interaction_hours)
        analysis.online_peak_hours = sorted([h for h, _ in hour_counter.most_common(5)])

        # Best posting hours (top 3)
        analysis.best_posting_hours = sorted([h for h, _ in hour_counter.most_common(3)])

        # Peak days
        day_counter = Counter(d for d in interaction_days if d in self.DAYS)
        analysis.engagement_peak_days = [d for d, _ in day_counter.most_common(3)]
        if day_counter:
            analysis.most_active_day = day_counter.most_common(1)[0][0]
            analysis.least_active_day = day_counter.most_common()[-1][0]

        # Interaction types
        if interaction_types:
            analysis.top_interaction_types = Counter(interaction_types).most_common(5)

        # Session interactions
        if session_interactions and len(session_interactions) >= 2:
            analysis.avg_interactions_per_session = round(
                sum(session_interactions) / len(session_interactions), 1
            )

        # Behavioral metrics
        total_interactions = len(interaction_hours)
        if total_interactions > 0:
            analysis.sharing_rate = round(
                interaction_types.count("share") / total_interactions * 100, 2
            ) if interaction_types else 0.0
            analysis.click_rate = round(
                interaction_types.count("click") / total_interactions * 100, 2
            ) if interaction_types else 0.0

        # Consistency: how spread out are interactions across hours
        if total_interactions > 1:
            mean = sum(interaction_hours) / total_interactions
            variance = sum((h - mean) ** 2 for h in interaction_hours) / total_interactions
            # Lower variance = more consistent
            analysis.behavior_consistency = round(
                max(0, min(10, 10 - (variance ** 0.5) / 2)), 2
            )

        # Confidence improves with more data
        analysis.confidence = round(min(1.0, total_interactions / 100), 2)

        self._analyses[profile_id] = analysis
        return analysis

    def get_analysis(self, profile_id: str) -> Optional[BehaviorAnalysis]:
        return self._analyses.get(profile_id)

    def predict_optimal_posting_time(self, profile_id: str) -> Optional[int]:
        """Predict the single best hour to post."""
        analysis = self._analyses.get(profile_id)
        if not analysis or not analysis.online_peak_hours:
            return None
        return analysis.online_peak_hours[0]

    def predict_best_day(self, profile_id: str) -> Optional[str]:
        """Predict the best day of week to post."""
        analysis = self._analyses.get(profile_id)
        if not analysis:
            return None
        return analysis.most_active_day or None

    def compare_segments(self, id_a: str, id_b: str) -> Dict:
        """Compare behavioral patterns of two audience segments."""
        a = self._analyses.get(id_a)
        b = self._analyses.get(id_b)
        if not a or not b:
            return {"error": "Missing analysis data"}

        return {
            "peak_hours_overlap": len(set(a.online_peak_hours) & set(b.online_peak_hours)),
            "peak_days_a": a.engagement_peak_days,
            "peak_days_b": b.engagement_peak_days,
            "consistency_var": round(a.behavior_consistency - b.behavior_consistency, 2),
            "device_a": a.active_device_preference,
            "device_b": b.active_device_preference,
            "best_day_a": a.most_active_day,
            "best_day_b": b.most_active_day,
        }
