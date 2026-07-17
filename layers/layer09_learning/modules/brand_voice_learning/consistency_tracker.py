"""Consistency Tracker — Track brand voice consistency across content."""
from __future__ import annotations
import itertools
from typing import Any, Dict, List

from layers.layer09_learning.modules.brand_voice_learning.brand_profile import BrandProfile

_CC_COUNTER = itertools.count(1)


class ConsistencyCheck:
    """Result of a consistency check for a single content piece."""

    __slots__ = ("content_id", "platform", "tone_match", "vocabulary_match",
                 "terminology_match", "style_match", "overall_score",
                 "violations", "recommendations")

    def __init__(self, content_id: str = "", platform: str = "") -> None:
        self.content_id: str = f"cc_{next(_CC_COUNTER)}"
        self.platform = platform
        self.tone_match: float = 0.0
        self.vocabulary_match: float = 0.0
        self.terminology_match: float = 0.0
        self.style_match: float = 0.0
        self.overall_score: float = 0.0
        self.violations: List[str] = []
        self.recommendations: List[str] = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "content_id": self.content_id,
            "platform": self.platform,
            "tone_match": round(self.tone_match, 3),
            "vocabulary_match": round(self.vocabulary_match, 3),
            "overall_score": round(self.overall_score, 3),
            "violation_count": len(self.violations),
        }


class ConsistencyTracker:
    """Track how consistently brand voice is applied."""

    def __init__(self) -> None:
        self._checks: List[ConsistencyCheck] = []

    def check_content(self, content: str, brand: BrandProfile,
                      platform: str = "") -> ConsistencyCheck:
        check = ConsistencyCheck()
        check.platform = platform
        lower = content.lower()
        check.tone_match = self._check_tone(lower, brand)
        check.vocabulary_match = self._check_vocabulary(lower, brand)
        check.terminology_match = self._check_terminology(lower, brand)
        check.style_match = self._check_style(lower, brand)
        check.overall_score = round(
            check.tone_match * 0.3 + check.vocabulary_match * 0.3 +
            check.terminology_match * 0.2 + check.style_match * 0.2,
            3,
        )
        check.violations = self._check_violations(lower, brand)
        check.recommendations = self._generate_recommendations(check, brand)
        self._checks.append(check)
        return check

    def _check_tone(self, lower: str, brand: BrandProfile) -> float:
        if not brand.tone_profile:
            return 0.5
        tone_keywords = {
            "professional": ["expert", "industry", "solution", "strategy"],
            "friendly": ["hello", "thanks", "awesome", "great"],
            "educational": ["learn", "discover", "tip", "guide"],
            "urgent": ["now", "today", "limited", "hurry"],
            "inspirational": ["inspire", "dream", "achieve", "success"],
            "casual": ["hey", "btw", "lol", "totally"],
        }
        score = 0.0
        for tone, weight in brand.tone_profile.items():
            keywords = tone_keywords.get(tone, [])
            if keywords:
                match = sum(1 for kw in keywords if kw in lower) / len(keywords)
                score += match * weight
        return round(min(1.0, score), 3)

    def _check_vocabulary(self, lower: str, brand: BrandProfile) -> float:
        if not brand.preferred_words:
            return 0.5
        matches = sum(1 for w in brand.preferred_words if w in lower)
        if brand.forbidden_words:
            violations = sum(1 for w in brand.forbidden_words if w in lower)
            penalty = violations * 0.1
            return round(max(0.0, min(1.0, matches / len(brand.preferred_words) - penalty)), 3)
        return round(min(1.0, matches / max(1, len(brand.preferred_words))), 3)

    def _check_terminology(self, lower: str, brand: BrandProfile) -> float:
        if not brand.terminology:
            return 0.5
        matches = sum(1 for term in brand.terminology if term.lower() in lower)
        return round(min(1.0, matches / max(1, len(brand.terminology))), 3)

    def _check_style(self, lower: str, brand: BrandProfile) -> float:
        score = 0.5
        if brand.emoji_style == "moderate":
            emoji_count = sum(1 for c in lower if ord(c) > 0x1F600)
            if 0 < emoji_count <= 3:
                score += 0.2
            elif emoji_count > 10:
                score -= 0.2
        if brand.formality_level == "high":
            formal = ["furthermore", "therefore", "consequently"]
            match = sum(1 for w in formal if w in lower)
            score += match * 0.1
        return round(min(1.0, max(0.0, score)), 3)

    def _check_violations(self, lower: str, brand: BrandProfile) -> List[str]:
        violations = []
        for word in brand.forbidden_words:
            if word in lower:
                violations.append(f"Forbidden word used: '{word}'")
        return violations

    def _generate_recommendations(self, check: ConsistencyCheck, brand: BrandProfile) -> List[str]:
        recs = []
        if check.overall_score < 0.5:
            recs.append("Consider revising content to better match brand voice")
        if check.tone_match < 0.3:
            recs.append("Adjust tone to match brand profile")
        if check.vocabulary_match < 0.3 and brand.preferred_words:
            recs.append("Use more preferred vocabulary from brand voice")
        return recs

    def get_checks(self) -> List[ConsistencyCheck]:
        return list(self._checks)

    def get_average_score(self) -> float:
        if not self._checks:
            return 0.0
        return round(sum(c.overall_score for c in self._checks) / len(self._checks), 3)

    def get_violations_count(self) -> int:
        return sum(len(c.violations) for c in self._checks)
