"""MistakeDetectionEngine — Detects failing patterns in titles, hashtags, timing, content."""
from __future__ import annotations
import threading
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple


class MistakePattern:
    __slots__ = ("id", "pattern_type", "description", "severity", "occurrences",
                 "affected_entities", "example_data", "detected_at", "status",
                 "suggested_fix", "confidence")

    SEVERITY_LEVELS = ("low", "medium", "high", "critical")

    def __init__(self, pattern_type: str, description: str,
                 severity: str = "medium") -> None:
        self.id = str(uuid.uuid4())[:12]
        self.pattern_type = pattern_type
        self.description = description
        self.severity = severity
        self.occurrences = 1
        self.affected_entities: List[str] = []
        self.example_data: List[Dict[str, Any]] = []
        self.detected_at = time.time()
        self.status = "active"
        self.suggested_fix = ""
        self.confidence = 0.0

    @property
    def priority_score(self) -> float:
        sev_map = {"critical": 40, "high": 30, "medium": 20, "low": 10}
        return sev_map.get(self.severity, 10) + min(self.occurrences * 2, 30) + self.confidence * 0.3

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id, "type": self.pattern_type,
            "description": self.description, "severity": self.severity,
            "occurrences": self.occurrences,
            "affected": len(self.affected_entities),
            "priority_score": round(self.priority_score, 1),
            "status": self.status, "fix": self.suggested_fix,
            "confidence": round(self.confidence, 1),
        }


class FailingTitle:
    __slots__ = ("title", "clicks", "impressions", "ctr", "engagement", "post_count")

    def __init__(self, title: str) -> None:
        self.title = title
        self.clicks = 0
        self.impressions = 0
        self.ctr = 0.0
        self.engagement = 0
        self.post_count = 0

    def to_dict(self) -> Dict[str, Any]:
        return {"title": self.title, "ctr": round(self.ctr, 2),
                "engagement": self.engagement, "posts": self.post_count}


class MistakeDetectionEngine:
    """Detects failing patterns: bad titles, weak hashtags, poor timing, low CTR."""
    _instance: Optional["MistakeDetectionEngine"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "MistakeDetectionEngine":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True
        self._patterns: Dict[str, MistakePattern] = {}
        self._failing_titles: Dict[str, FailingTitle] = {}
        self._failing_hashtags: Dict[str, Dict[str, Any]] = {}
        self._failing_times: Dict[str, Dict[str, Any]] = {}
        self._detection_history: List[Dict[str, Any]] = []

    def detect_title_pattern(self, title: str, ctr: float, engagement: float,
                             post_id: str = "") -> Optional[MistakePattern]:
        if ctr < 1.0 and engagement < 2.0:
            key = title.lower()[:50]
            if key not in self._failing_titles:
                self._failing_titles[key] = FailingTitle(title)
            ft = self._failing_titles[key]
            ft.clicks += 1
            ft.ctr = ctr
            ft.engagement = engagement
            ft.post_count += 1

            if ft.post_count >= 2:
                pattern = self._find_or_create_pattern(
                    "failing_title",
                    f"Title '{title[:50]}...' consistently underperforms (CTR={ctr}%)",
                    "high",
                )
                pattern.occurrences += 1
                if post_id:
                    pattern.affected_entities.append(post_id)
                pattern.confidence = min(ft.post_count * 15, 95)
                pattern.suggested_fix = "Try different headline style: numbers, questions, or power words"
                return pattern
        return None

    def detect_hashtag_pattern(self, hashtag: str, impressions: int,
                               engagement: int) -> Optional[MistakePattern]:
        eng_rate = (engagement / impressions * 100) if impressions > 0 else 0
        if eng_rate < 0.5 and impressions > 100:
            if hashtag not in self._failing_hashtags:
                self._failing_hashtags[hashtag] = {
                    "hashtag": hashtag, "impressions": 0,
                    "engagement": 0, "count": 0,
                }
            h = self._failing_hashtags[hashtag]
            h["impressions"] += impressions
            h["engagement"] += engagement
            h["count"] += 1
            if h["count"] >= 3:
                pattern = self._find_or_create_pattern(
                    "weak_hashtag",
                    f"Hashtag '{hashtag}' consistently low engagement ({eng_rate:.1f}%)",
                    "medium",
                )
                pattern.occurrences = h["count"]
                pattern.suggested_fix = "Replace with trending or niche-specific hashtags"
                return pattern
        return None

    def detect_timing_pattern(self, hour: int, day_of_week: str,
                              ctr: float, platform: str = "") -> Optional[MistakePattern]:
        key = f"{day_of_week}_{hour}"
        if key not in self._failing_times:
            self._failing_times[key] = {
                "time": key, "platform": platform,
                "ctrs": [], "count": 0,
            }
        t = self._failing_times[key]
        t["ctrs"].append(ctr)
        t["count"] += 1
        if t["count"] >= 3:
            avg_ctr = sum(t["ctrs"]) / len(t["ctrs"])
            if avg_ctr < 1.0:
                pattern = self._find_or_create_pattern(
                    "bad_timing",
                    f"Posting at {day_of_week} {hour}:00 consistently low CTR ({avg_ctr:.1f}%)",
                    "medium",
                )
                pattern.occurrences = t["count"]
                pattern.suggested_fix = "Test different posting times or use scheduler"
                return pattern
        return None

    def detect_content_pattern(self, content_type: str, performance_score: float,
                               platform: str = "", niche: str = "") -> Optional[MistakePattern]:
        if performance_score < 20:
            pattern = self._find_or_create_pattern(
                "weak_content_type",
                f"Content type '{content_type}' on {platform} scores very low ({performance_score:.1f})",
                "high",
            )
            pattern.suggested_fix = f"Reduce '{content_type}' posts, try other formats"
            return pattern
        return None

    def _find_or_create_pattern(self, ptype: str, desc: str,
                                severity: str) -> MistakePattern:
        for p in self._patterns.values():
            if p.pattern_type == ptype and p.status == "active":
                return p
        pattern = MistakePattern(ptype, desc, severity)
        self._patterns[pattern.id] = pattern
        return pattern

    def get_pattern(self, pattern_id: str) -> Optional[MistakePattern]:
        return self._patterns.get(pattern_id)

    def get_active_patterns(self, severity: str = "") -> List[MistakePattern]:
        patterns = [p for p in self._patterns.values() if p.status == "active"]
        if severity:
            patterns = [p for p in patterns if p.severity == severity]
        return sorted(patterns, key=lambda p: p.priority_score, reverse=True)

    def get_failing_titles(self, limit: int = 10) -> List[FailingTitle]:
        return sorted(self._failing_titles.values(),
                      key=lambda t: t.ctr)[:limit]

    def resolve_pattern(self, pattern_id: str) -> bool:
        p = self._patterns.get(pattern_id)
        if p:
            p.status = "resolved"
            return True
        return False

    def get_detection_report(self) -> Dict[str, Any]:
        patterns = list(self._patterns.values())
        return {
            "total_patterns": len(patterns),
            "active": sum(1 for p in patterns if p.status == "active"),
            "resolved": sum(1 for p in patterns if p.status == "resolved"),
            "by_severity": {s: sum(1 for p in patterns if p.severity == s)
                           for s in MistakePattern.SEVERITY_LEVELS},
            "by_type": {},
            "failing_titles": len(self._failing_titles),
            "failing_hashtags": len(self._failing_hashtags),
            "failing_times": len(self._failing_times),
            "top_patterns": [p.to_dict() for p in self.get_active_patterns()[:5]],
        }

    def stats(self) -> Dict[str, Any]:
        return {
            "patterns": len(self._patterns),
            "failing_titles": len(self._failing_titles),
            "failing_hashtags": len(self._failing_hashtags),
            "failing_times": len(self._failing_times),
        }


def get_mistake_detection() -> MistakeDetectionEngine:
    return MistakeDetectionEngine()
