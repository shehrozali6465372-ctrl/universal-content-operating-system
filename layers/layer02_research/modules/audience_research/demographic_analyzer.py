"""
Demographic Analyzer
Layer 2: Research Engine — Module 4

Analyzes audience demographics:
- Age distribution analysis
- Gender split analysis
- Location analysis
- Language analysis
- Device usage analysis
- Socioeconomic profiling
"""

from collections import Counter
from typing import Dict, List, Optional


class DemographicProfile:
    """Computed demographic insights."""

    __slots__ = (
        "profile_id", "age_distribution", "gender_distribution",
        "location_distribution", "language_distribution",
        "device_distribution", "age_group_primary",
        "gender_primary", "top_locations", "top_languages",
        "mobile_first", "diversity_score", "concentration_score",
        "data_completeness", "confidence",
    )

    AGE_GROUPS = {
        "13-17": "teen", "18-24": "young_adult",
        "25-34": "adult", "35-44": "mature",
        "45-54": "senior", "55-65": "elder", "65+": "senior",
    }

    def __init__(self, profile_id: str):
        self.profile_id = profile_id
        self.age_distribution: Dict[str, int] = {}
        self.gender_distribution: Dict[str, float] = {}
        self.location_distribution: Dict[str, int] = {}
        self.language_distribution: Dict[str, int] = {}
        self.device_distribution: Dict[str, float] = {}
        self.age_group_primary = ""
        self.gender_primary = ""
        self.top_locations: List[str] = []
        self.top_languages: List[str] = []
        self.mobile_first = False
        self.diversity_score = 0.0
        self.concentration_score = 0.0
        self.data_completeness = 0.0
        self.confidence = 0.5

    def to_dict(self) -> dict:
        return {
            "profile_id": self.profile_id,
            "age_distribution": self.age_distribution,
            "gender_distribution": self.gender_distribution,
            "location_distribution": self.location_distribution,
            "language_distribution": self.language_distribution,
            "device_distribution": self.device_distribution,
            "age_group_primary": self.age_group_primary,
            "gender_primary": self.gender_primary,
            "top_locations": self.top_locations,
            "top_languages": self.top_languages,
            "mobile_first": self.mobile_first,
            "diversity_score": self.diversity_score,
            "concentration_score": self.concentration_score,
            "data_completeness": self.data_completeness,
            "confidence": self.confidence,
        }


class DemographicAnalyzer:
    """Analyze audience demographic data."""

    def __init__(self):
        self._profiles: Dict[str, DemographicProfile] = {}

    def analyze(
        self,
        profile_id: str,
        ages: Optional[List[int]] = None,
        genders: Optional[List[str]] = None,
        locations: Optional[List[str]] = None,
        languages: Optional[List[str]] = None,
        devices: Optional[List[str]] = None,
    ) -> DemographicProfile:
        """Full demographic analysis."""
        dp = DemographicProfile(profile_id)
        fields_present = 0
        total_fields = 5

        # Age analysis
        if ages:
            fields_present += 1
            age_counter = Counter(ages)
            dp.age_distribution = dict(age_counter.most_common())

            # Primary age group
            age_groups: Dict[str, int] = Counter()
            for age in ages:
                if 13 <= age <= 17:
                    age_groups["teen"] += 1
                elif 18 <= age <= 24:
                    age_groups["young_adult"] += 1
                elif 25 <= age <= 34:
                    age_groups["adult"] += 1
                elif 35 <= age <= 44:
                    age_groups["mature"] += 1
                elif 45 <= age <= 54:
                    age_groups["senior"] += 1
                else:
                    age_groups["elder"] += 1
            if age_groups:
                dp.age_group_primary = age_groups.most_common(1)[0][0]

        # Gender analysis
        if genders:
            fields_present += 1
            total = len(genders)
            gender_counter = Counter(genders)
            dp.gender_distribution = {g: round(c / total * 100, 1) for g, c in gender_counter.items()}
            dp.gender_primary = gender_counter.most_common(1)[0][0]

        # Location analysis
        if locations:
            fields_present += 1
            loc_counter = Counter(locations)
            dp.location_distribution = dict(loc_counter.most_common(20))
            dp.top_locations = [l for l, _ in loc_counter.most_common(5)]

        # Language analysis
        if languages:
            fields_present += 1
            lang_counter = Counter(languages)
            dp.language_distribution = dict(lang_counter.most_common(10))
            dp.top_languages = [l for l, _ in lang_counter.most_common(5)]

        # Device analysis
        if devices:
            fields_present += 1
            total = len(devices)
            dev_counter = Counter(devices)
            dp.device_distribution = {d: round(c / total * 100, 1) for d, c in dev_counter.items()}
            dp.mobile_first = dev_counter.get("mobile", 0) > dev_counter.get("desktop", 0)

        # Data completeness
        dp.data_completeness = round(fields_present / total_fields, 2)

        # Diversity score: how spread out the demographics are
        if dp.gender_distribution:
            values = list(dp.gender_distribution.values())
            if len(values) > 1:
                max_val = max(values)
                dp.diversity_score = round(min(10.0, (1 - abs(max_val - 50) / 50) * 10), 2)

        # Concentration: how concentrated in one group
        if dp.location_distribution:
            total_locs = sum(dp.location_distribution.values())
            if total_locs > 0:
                max_loc = max(dp.location_distribution.values())
                dp.concentration_score = round(max_loc / total_locs * 10, 2)

        # Confidence
        dp.confidence = round(dp.data_completeness * 0.8 + (0.2 if ages and len(ages) >= 10 else 0), 2)

        self._profiles[profile_id] = dp
        return dp

    def get_profile(self, profile_id: str) -> Optional[DemographicProfile]:
        return self._profiles.get(profile_id)

    def find_segments(self, profile_id: str) -> List[Dict[str, any]]:
        """Identify demographic segments within the audience."""
        dp = self._profiles.get(profile_id)
        if not dp:
            return []

        segments = []
        # Age-based segments
        if dp.age_group_primary:
            segments.append({
                "type": "age", "segment": dp.age_group_primary,
                "dominance": "primary",
            })
        if dp.gender_primary:
            segments.append({
                "type": "gender", "segment": dp.gender_primary,
                "dominance": "primary",
            })
        for loc in dp.top_locations[:3]:
            segments.append({
                "type": "location", "segment": loc,
                "dominance": "regional",
            })
        return segments
