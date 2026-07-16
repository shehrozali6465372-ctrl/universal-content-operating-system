"""Vocabulary Checker — Verify brand vocabulary consistency."""
from __future__ import annotations
import re

from layers.layer06_quality.modules.brand_voice_engine.brand_profile import BrandProfile
from layers.layer06_quality.modules.brand_voice_engine.voice_report import VoiceComponentScore, VoiceIssue


class VocabularyChecker:
    """Check content vocabulary against brand profile."""

    def __init__(self) -> None:
        self._check_count = 0

    def check(self, content: str, profile: BrandProfile) -> VoiceComponentScore:
        """Check vocabulary consistency."""
        result = VoiceComponentScore(component="vocabulary")
        content_lower = content.lower()
        score = 1.0

        # Check forbidden words
        for word in profile.forbidden_words:
            if word.lower() in content_lower:
                score -= 0.2
                result.issues.append(VoiceIssue(
                    category="vocabulary", severity="critical",
                    description=f"Forbidden word '{word}' found in content",
                    suggestion=f"Remove or replace '{word}' with approved alternative",
                    current_value=word,
                    expected_value="not present",
                ))

        # Check preferred words usage
        if profile.preferred_words:
            used_preferred = sum(1 for w in profile.preferred_words if w.lower() in content_lower)
            if profile.preferred_words and used_preferred == 0:
                score -= 0.1
                result.issues.append(VoiceIssue(
                    category="vocabulary", severity="low",
                    description="No brand-preferred words used",
                    suggestion=f"Consider using: {', '.join(profile.preferred_words[:3])}",
                ))

        # Check terminology enforcement
        for term, preferred_form in profile.terminology.items():
            if term.lower() in content_lower and preferred_form.lower() not in content_lower:
                score -= 0.15
                result.issues.append(VoiceIssue(
                    category="terminology", severity="medium",
                    description=f"'{term}' used instead of preferred '{preferred_form}'",
                    suggestion=f"Replace '{term}' with '{preferred_form}'",
                    current_value=term,
                    expected_value=preferred_form,
                ))

        # Check brand vocabulary presence
        if profile.vocabulary:
            brand_words = set(w.lower() for w in profile.vocabulary)
            content_words = set(re.findall(r'\b\w+\b', content_lower))
            overlap = brand_words & content_words
            coverage = len(overlap) / len(brand_words) if brand_words else 0
            if coverage < 0.1:
                score -= 0.05
                result.issues.append(VoiceIssue(
                    category="vocabulary", severity="low",
                    description=f"Low brand vocabulary usage ({coverage:.0%})",
                    suggestion="Incorporate more brand-specific vocabulary",
                ))

        result.score = max(0.0, min(1.0, score))
        result.compute_status()
        self._check_count += 1
        return result

    @property
    def check_count(self) -> int:
        return self._check_count
