"""Tone Checker — Verify content tone matches brand personality."""
from __future__ import annotations
import re
from typing import Dict

from layers.layer06_quality.modules.brand_voice_engine.brand_profile import BrandProfile
from layers.layer06_quality.modules.brand_voice_engine.voice_report import VoiceComponentScore, VoiceIssue


FORMAL_MARKERS = {
    "furthermore", "consequently", "therefore", "nevertheless",
    "moreover", "henceforth", "accordingly", "hence",
    "notwithstanding", "aforementioned", "hereafter",
}

CASUAL_MARKERS = {
    "gonna", "wanna", "gotta", "kinda", "sorta", "yeah", "yep",
    "nope", "hey", "hi", "wow", "cool", "awesome", "amazing",
    "lol", "omg", "btw", "tbh", "imo", "smh", "fyi",
}

HUMOR_MARKERS = {
    "haha", "lol", "lmao", "rofl", "joke", "funny", "hilarious",
    "pun", "irony", "sarcasm", "witty",
}

PROFESSIONAL_MARKERS = {
    "analyze", "strategy", "implementation", "optimize",
    "leverage", "stakeholder", "deliverable", "benchmark",
    "roi", "kpi", "metrics", "insights", "data-driven",
}


class ToneChecker:
    """Check content tone against brand profile."""

    def __init__(self) -> None:
        self._check_count = 0

    def check(self, content: str, profile: BrandProfile) -> VoiceComponentScore:
        """Check if content tone matches brand profile."""
        result = VoiceComponentScore(component="tone")
        content_lower = content.lower()
        words = set(re.findall(r'\b\w+\b', content_lower))

        detected_tones = self._detect_tones(words, content_lower)
        expected_tone = profile.tone

        score = 1.0
        if expected_tone == "formal":
            formal_hits = len(words & FORMAL_MARKERS)
            casual_hits = len(words & CASUAL_MARKERS)
            if casual_hits > 0:
                score -= casual_hits * 0.15
                result.issues.append(VoiceIssue(
                    category="tone", severity="medium",
                    description="Casual language detected in formal brand voice",
                    suggestion="Replace casual terms with formal alternatives",
                    current_value=f"{casual_hits} casual markers",
                    expected_value="formal language",
                ))
        elif expected_tone == "casual":
            formal_hits = len(words & FORMAL_MARKERS)
            if formal_hits > 2:
                score -= formal_hits * 0.1
                result.issues.append(VoiceIssue(
                    category="tone", severity="low",
                    description="Too many formal terms for casual brand voice",
                    suggestion="Simplify language for casual tone",
                ))
        elif expected_tone == "professional":
            casual_hits = len(words & CASUAL_MARKERS)
            if casual_hits > 1:
                score -= casual_hits * 0.12
                result.issues.append(VoiceIssue(
                    category="tone", severity="medium",
                    description="Casual abbreviations detected in professional brand",
                    suggestion="Replace abbreviations with full words",
                ))
        elif expected_tone == "humorous":
            humor_hits = len(words & HUMOR_MARKERS)
            if humor_hits == 0:
                score -= 0.2
                result.issues.append(VoiceIssue(
                    category="tone", severity="low",
                    description="No humor signals detected for humorous brand voice",
                    suggestion="Add light humor or wit to match brand personality",
                ))

        result.score = max(0.0, score)
        result.compute_status()
        self._check_count += 1
        return result

    def _detect_tones(self, words: set, text: str) -> Dict[str, int]:
        return {
            "formal": len(words & FORMAL_MARKERS),
            "casual": len(words & CASUAL_MARKERS),
            "professional": len(words & PROFESSIONAL_MARKERS),
            "humorous": len(words & HUMOR_MARKERS),
        }

    @property
    def check_count(self) -> int:
        return self._check_count
