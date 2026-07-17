"""Pattern Learner — Detect recurring patterns, best combos, recommendations."""
from __future__ import annotations
from typing import Any, Dict, List

from layers.layer07_publishing.modules.publishing_memory.publish_history import PublishRecord


class Pattern:
    """A detected recurring pattern."""

    __slots__ = ("pattern_type", "description", "confidence",
                 "frequency", "example_data")

    def __init__(self, pattern_type: str = "", description: str = "") -> None:
        self.pattern_type = pattern_type
        self.description = description
        self.confidence: float = 0.0
        self.frequency: int = 0
        self.example_data: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pattern_type": self.pattern_type,
            "description": self.description,
            "confidence": round(self.confidence, 3),
            "frequency": self.frequency,
            "example_data": self.example_data,
        }


class PatternLearner:
    """Detect recurring patterns and generate recommendations."""

    MIN_FREQUENCY = 3

    def __init__(self) -> None:
        self._patterns: List[Pattern] = []

    def detect_patterns(self, records: List[PublishRecord]) -> List[Pattern]:
        self._patterns.clear()
        if len(records) < self.MIN_FREQUENCY:
            return self._patterns

        self._detect_platform_patterns(records)
        self._detect_content_type_patterns(records)
        self._detect_time_patterns(records)
        self._detect_tag_patterns(records)

        return list(self._patterns)

    def get_recommendations(self, records: List[PublishRecord]) -> List[Dict[str, Any]]:
        self.detect_patterns(records)
        recs: List[Dict[str, Any]] = []
        for p in self._patterns:
            if p.confidence >= 0.5:
                recs.append({
                    "type": p.pattern_type,
                    "recommendation": p.description,
                    "confidence": p.confidence,
                    "frequency": p.frequency,
                })
        return sorted(recs, key=lambda r: r["confidence"], reverse=True)

    def get_best_combination(self, records: List[PublishRecord]) -> Dict[str, Any]:
        if not records:
            return {"platform": "", "content_type": "", "hour": -1}
        combos: Dict[str, List[PublishRecord]] = {}
        for r in records:
            key = f"{r.platform}_{r.content_type}"
            combos.setdefault(key, []).append(r)
        best_key = max(combos, key=lambda k: len(combos[k]))
        parts = best_key.split("_", 1)
        return {
            "platform": parts[0],
            "content_type": parts[1] if len(parts) > 1 else "",
            "count": len(combos[best_key]),
        }

    def _detect_platform_patterns(self, records: List[PublishRecord]) -> None:
        platform_counts: Dict[str, int] = {}
        for r in records:
            platform_counts[r.platform] = platform_counts.get(r.platform, 0) + 1
        for platform, count in platform_counts.items():
            if count >= self.MIN_FREQUENCY:
                conf = min(1.0, count / max(1, len(records)))
                p = Pattern("platform_preference", f"{platform} is the most used platform ({count} posts)")
                p.confidence = round(conf, 3)
                p.frequency = count
                p.example_data["platform"] = platform
                self._patterns.append(p)

    def _detect_content_type_patterns(self, records: List[PublishRecord]) -> None:
        type_counts: Dict[str, int] = {}
        for r in records:
            type_counts[r.content_type] = type_counts.get(r.content_type, 0) + 1
        for ct, count in type_counts.items():
            if count >= self.MIN_FREQUENCY:
                conf = min(1.0, count / max(1, len(records)))
                p = Pattern("content_type_preference", f"'{ct}' is the most used content type ({count} posts)")
                p.confidence = round(conf, 3)
                p.frequency = count
                p.example_data["content_type"] = ct
                self._patterns.append(p)

    def _detect_time_patterns(self, records: List[PublishRecord]) -> None:
        hour_counts: Dict[int, int] = {}
        for r in records:
            hour = r.get_hour()
            hour_counts[hour] = hour_counts.get(hour, 0) + 1
        for hour, count in hour_counts.items():
            if count >= self.MIN_FREQUENCY:
                conf = min(1.0, count / max(1, len(records)))
                p = Pattern("time_preference", f"Hour {hour}:00 is preferred ({count} posts)")
                p.confidence = round(conf, 3)
                p.frequency = count
                p.example_data["hour"] = hour
                self._patterns.append(p)

    def _detect_tag_patterns(self, records: List[PublishRecord]) -> None:
        tag_counts: Dict[str, int] = {}
        for r in records:
            for tag in r.tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        for tag, count in tag_counts.items():
            if count >= self.MIN_FREQUENCY:
                conf = min(1.0, count / max(1, len(records)))
                p = Pattern("tag_preference", f"Tag '{tag}' is frequently used ({count} posts)")
                p.confidence = round(conf, 3)
                p.frequency = count
                p.example_data["tag"] = tag
                self._patterns.append(p)

    @property
    def pattern_count(self) -> int:
        return len(self._patterns)
