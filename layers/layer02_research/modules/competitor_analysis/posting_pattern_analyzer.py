"""
Posting Pattern Analyzer
Layer 2: Research Engine — Module 3

Analyzes when and how often competitors post:
- Posting frequency analysis
- Best posting times detection
- Day-of-week patterns
- Gap detection (dead zones)
- Consistency scoring
"""

from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from layers.layer02_research.modules.competitor_analysis.content_analyzer import ContentPost


class PostingPattern:
    """Results of posting pattern analysis for one competitor."""

    __slots__ = (
        "competitor_id", "avg_posts_per_day", "avg_posts_per_week",
        "posting_frequency", "best_hours", "best_days",
        "hourly_distribution", "daily_distribution",
        "consistency_score", "dead_zones",
        "posting_streak_avg", "gap_avg_hours",
    )

    def __init__(self, competitor_id: str):
        self.competitor_id = competitor_id
        self.avg_posts_per_day = 0.0
        self.avg_posts_per_week = 0.0
        self.posting_frequency = "unknown"
        self.best_hours: List[int] = []
        self.best_days: List[str] = []
        self.hourly_distribution: Dict[int, int] = {}
        self.daily_distribution: Dict[str, int] = {}
        self.consistency_score = 0.0
        self.dead_zones: List[str] = []
        self.posting_streak_avg = 0.0
        self.gap_avg_hours = 0.0

    def to_dict(self) -> dict:
        return {
            "competitor_id": self.competitor_id,
            "avg_posts_per_day": self.avg_posts_per_day,
            "avg_posts_per_week": self.avg_posts_per_week,
            "posting_frequency": self.posting_frequency,
            "best_hours": self.best_hours,
            "best_days": self.best_days,
            "hourly_distribution": self.hourly_distribution,
            "daily_distribution": self.daily_distribution,
            "consistency_score": self.consistency_score,
            "dead_zones": self.dead_zones,
            "posting_streak_avg": self.posting_streak_avg,
            "gap_avg_hours": self.gap_avg_hours,
        }


class PostingPatternAnalyzer:
    """Analyze posting patterns of competitors."""

    DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    def __init__(self):
        self._patterns: Dict[str, PostingPattern] = {}

    def analyze(self, competitor_id: str, posts: List[ContentPost]) -> PostingPattern:
        """Full posting pattern analysis."""
        pattern = PostingPattern(competitor_id)

        if not posts:
            self._patterns[competitor_id] = pattern
            return pattern

        # Hourly distribution
        hourly = Counter()
        daily = Counter()
        timestamps = []

        for post in posts:
            if post.posted_at:
                try:
                    dt = datetime.fromisoformat(post.posted_at.replace("Z", "+00:00"))
                    hourly[dt.hour] += 1
                    daily[self.DAY_NAMES[dt.weekday()]] += 1
                    timestamps.append(dt)
                except (ValueError, TypeError):
                    continue

        pattern.hourly_distribution = dict(sorted(hourly.items()))
        pattern.daily_distribution = dict(daily)

        # Best hours (top 3)
        pattern.best_hours = [h for h, _ in hourly.most_common(3)]

        # Best days (top 2)
        pattern.best_days = [d for d, _ in daily.most_common(2)]

        # Frequency calculation
        timestamps.sort()
        if len(timestamps) >= 2:
            span_days = max((timestamps[-1] - timestamps[0]).total_seconds() / 86400, 1)
            pattern.avg_posts_per_day = round(len(timestamps) / span_days, 2)
            pattern.avg_posts_per_week = round(pattern.avg_posts_per_day * 7, 1)

            # Gap analysis
            gaps = []
            for i in range(1, len(timestamps)):
                gap = (timestamps[i] - timestamps[i - 1]).total_seconds() / 3600
                gaps.append(gap)
            pattern.gap_avg_hours = round(sum(gaps) / len(gaps), 1) if gaps else 0
        else:
            pattern.avg_posts_per_day = 0
            pattern.avg_posts_per_week = 0

        # Frequency label
        if pattern.avg_posts_per_day >= 5:
            pattern.posting_frequency = "very_high"
        elif pattern.avg_posts_per_day >= 2:
            pattern.posting_frequency = "high"
        elif pattern.avg_posts_per_day >= 0.8:
            pattern.posting_frequency = "medium"
        elif pattern.avg_posts_per_day >= 0.3:
            pattern.posting_frequency = "low"
        elif pattern.avg_posts_per_day > 0:
            pattern.posting_frequency = "very_low"
        else:
            pattern.posting_frequency = "inactive"

        # Consistency: how evenly spread across days
        if daily:
            values = list(daily.values())
            if len(values) > 1:
                mean = sum(values) / len(values)
                variance = sum((v - mean) ** 2 for v in values) / len(values)
                # Low variance = high consistency
                pattern.consistency_score = round(max(0, 10 - (variance ** 0.5)), 2)
            else:
                pattern.consistency_score = 5.0

        # Dead zones: hours with zero posts
        all_hours = set(range(24))
        active_hours = set(hourly.keys())
        dead = sorted(all_hours - active_hours)
        if dead:
            # Group consecutive dead hours
            ranges = []
            start = dead[0]
            prev = dead[0]
            for h in dead[1:]:
                if h == prev + 1:
                    prev = h
                else:
                    ranges.append(f"{start:02d}:00-{prev+1:02d}:00" if start != prev else f"{start:02d}:00")
                    start = h
                    prev = h
            ranges.append(f"{start:02d}:00-{prev+1:02d}:00" if start != prev else f"{start:02d}:00")
            pattern.dead_zones = ranges

        self._patterns[competitor_id] = pattern
        return pattern

    def get_pattern(self, competitor_id: str) -> Optional[PostingPattern]:
        return self._patterns.get(competitor_id)

    def find_gap_windows(
        self, competitor_id: str, min_gap_hours: int = 4
    ) -> List[Tuple[int, int]]:
        """Find posting gap windows we can exploit."""
        pattern = self._patterns.get(competitor_id)
        if not pattern:
            return []

        gaps = []
        active = sorted(pattern.hourly_distribution.keys())
        if not active:
            return [(0, 24)]

        # Check wrap-around gap
        if active[0] != 0:
            gaps.append((0, active[0]))
        for i in range(len(active) - 1):
            gap = active[i + 1] - active[i]
            if gap >= min_gap_hours:
                gaps.append((active[i], active[i + 1]))

        # Check end gap
        if active[-1] != 23:
            gaps.append((active[-1], 24))

        return gaps

    def compare_patterns(
        self, comp_a: str, comp_b: str
    ) -> Dict[str, any]:
        """Compare posting patterns between two competitors."""
        pa = self._patterns.get(comp_a)
        pb = self._patterns.get(comp_b)
        if not pa or not pb:
            return {"error": "Missing pattern data"}

        return {
            "frequency_diff": round(pa.avg_posts_per_day - pb.avg_posts_per_day, 2),
            "consistency_diff": round(pa.consistency_score - pb.consistency_score, 2),
            "shared_hours": sorted(set(pa.best_hours) & set(pb.best_hours)),
            "unique_hours_a": sorted(set(pa.best_hours) - set(pb.best_hours)),
            "unique_hours_b": sorted(set(pb.best_hours) - set(pa.best_hours)),
            "shared_days": sorted(set(pa.best_days) & set(pb.best_days)),
            "dead_zones_a": pa.dead_zones,
            "dead_zones_b": pb.dead_zones,
        }

    def get_exploitable_hours(self, competitor_id: str) -> List[int]:
        """Find hours when competitor is inactive (our opportunity)."""
        pattern = self._patterns.get(competitor_id)
        if not pattern:
            return list(range(24))
        active_hours = set(pattern.hourly_distribution.keys())
        return sorted(set(range(24)) - active_hours)
