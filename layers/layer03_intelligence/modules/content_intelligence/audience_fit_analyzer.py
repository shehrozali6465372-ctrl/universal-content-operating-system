"""Audience Fit Analyzer - Measures content-audience alignment."""
from __future__ import annotations
from typing import Dict, List


class AudienceFitResult:
    __slots__ = ("fit_score", "matched_segments", "missed_segments",
                 "reading_level_match", "interest_match", "recommendations")
    def __init__(self) -> None:
        self.fit_score = 0.0
        self.matched_segments: List[str] = []
        self.missed_segments: List[str] = []
        self.reading_level_match = 0.0
        self.interest_match = 0.0
        self.recommendations: List[str] = []
    def to_dict(self) -> Dict:
        return {
            "fit_score": round(self.fit_score, 3),
            "matched_segments": list(self.matched_segments),
            "missed_segments": list(self.missed_segments),
            "reading_level_match": round(self.reading_level_match, 3),
            "interest_match": round(self.interest_match, 3),
            "recommendations": list(self.recommendations),
        }


class AudienceFitAnalyzer:
    def analyze(self, content: str, audience: Dict) -> AudienceFitResult:
        result = AudienceFitResult()
        content_lower = content.lower()
        words = set(content_lower.split())
        interests = audience.get("interests", [])
        if interests:
            matched = sum(1 for i in interests if any(w in content_lower for w in i.lower().split()))
            result.interest_match = matched / max(len(interests), 1)
        avg_word_len = sum(len(w) for w in content.split()) / max(len(content.split()), 1)
        target_level = audience.get("reading_level", "moderate")
        level_map = {"easy": 4, "moderate": 6, "advanced": 8}
        target_avg = level_map.get(target_level, 6)
        result.reading_level_match = max(0, 1.0 - abs(avg_word_len - target_avg) / target_avg)
        segments = audience.get("segments", [])
        for seg in segments:
            seg_words = set(seg.lower().split())
            if len(seg_words & words) > 0:
                result.matched_segments.append(seg)
            else:
                result.missed_segments.append(seg)
        seg_match = len(result.matched_segments) / max(len(segments), 1) if segments else 0.5
        result.fit_score = result.interest_match * 0.4 + result.reading_level_match * 0.3 + seg_match * 0.3
        if result.interest_match < 0.5: result.recommendations.append("Add content relevant to audience interests")
        if result.reading_level_match < 0.7: result.recommendations.append("Adjust reading level")
        return result
