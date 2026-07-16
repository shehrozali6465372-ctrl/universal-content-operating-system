"""Brand Voice Engine — Core orchestrator for brand voice consistency checking."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional

from layers.layer06_quality.modules.brand_voice_engine.brand_profile import BrandProfile, create_default_profile
from layers.layer06_quality.modules.brand_voice_engine.tone_checker import ToneChecker
from layers.layer06_quality.modules.brand_voice_engine.vocabulary_checker import VocabularyChecker
from layers.layer06_quality.modules.brand_voice_engine.style_analyzer import StyleAnalyzer
from layers.layer06_quality.modules.brand_voice_engine.voice_report import VoiceReport


class BrandVoiceEngine:
    """Orchestrates full brand voice consistency pipeline."""

    def __init__(
        self,
        tone_checker: Optional[ToneChecker] = None,
        vocabulary_checker: Optional[VocabularyChecker] = None,
        style_analyzer: Optional[StyleAnalyzer] = None,
    ) -> None:
        self.tone_checker = tone_checker or ToneChecker()
        self.vocabulary_checker = vocabulary_checker or VocabularyChecker()
        self.style_analyzer = style_analyzer or StyleAnalyzer()
        self._check_count = 0

    def check(self, content: str, profile: Optional[BrandProfile] = None) -> VoiceReport:
        """Full brand voice check pipeline."""
        if profile is None:
            profile = create_default_profile()

        report = VoiceReport(brand_name=profile.brand_name)
        start_time = time.time()

        # 1. Tone check
        tone_score = self.tone_checker.check(content, profile)
        report.component_scores.append(tone_score)
        report.issues.extend(tone_score.issues)

        # 2. Vocabulary check
        vocab_score = self.vocabulary_checker.check(content, profile)
        report.component_scores.append(vocab_score)
        report.issues.extend(vocab_score.issues)

        # 3. Style analysis (emoji, hashtags, CTA, sentences)
        style_score = self.style_analyzer.check(content, profile)
        report.component_scores.append(style_score)
        report.issues.extend(style_score.issues)

        report.compute_overall()

        elapsed = time.time() - start_time
        report.statistics["check_time_ms"] = round(elapsed * 1000, 2)
        report.statistics["content_length"] = len(content)

        self._check_count += 1
        return report

    def check_quick(self, content: str, profile: Optional[BrandProfile] = None) -> Dict[str, Any]:
        """Quick brand voice check returning summary."""
        report = self.check(content, profile)
        return {
            "brand_name": report.brand_name,
            "overall_score": report.overall_score,
            "is_consistent": report.is_consistent,
            "issue_count": len(report.issues),
            "critical_issues": report.statistics.get("critical_issues", 0),
        }

    def check_batch(
        self, contents: List[str], profile: Optional[BrandProfile] = None,
    ) -> List[VoiceReport]:
        """Check multiple content pieces."""
        return [self.check(c, profile) for c in contents]

    @property
    def check_count(self) -> int:
        return self._check_count
