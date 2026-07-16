"""Style Analyzer — Analyze writing style, emoji use, formatting, CTA, and sentence structure."""
from __future__ import annotations
import re
from typing import Dict, List

from layers.layer06_quality.modules.brand_voice_engine.brand_profile import BrandProfile
from layers.layer06_quality.modules.brand_voice_engine.voice_report import VoiceComponentScore, VoiceIssue


CTA_PATTERNS: Dict[str, List[str]] = {
    "soft": ["learn more", "find out", "see how", "get started", "try now", "explore"],
    "direct": ["buy now", "sign up", "join", "subscribe", "download", "order"],
    "question": ["what do you think", "your thoughts", "have you tried", "interested in", "ready for"],
    "none": [],
}

EMOJI_STYLE_PATTERNS = {
    "minimal": [r'[😊👍👏💡📊]'],
    "moderate": [r'[😊👍👏💡📊🔥💪✨🎉💯🚀❤️]'],
    "heavy": [r'[😊👍👏💡📊🔥💪✨🎉💯🚀❤️😍🤩🙌🎯💥🆒🌟💫]'],
}


class StyleAnalyzer:
    """Analyze writing style consistency."""

    def __init__(self) -> None:
        self._check_count = 0

    def check(self, content: str, profile: BrandProfile) -> VoiceComponentScore:
        """Check multi-dimensional style consistency."""
        result = VoiceComponentScore(component="style")
        score = 1.0

        # Emoji style check
        emoji_issues = self._check_emoji(content, profile)
        for issue in emoji_issues:
            result.issues.append(issue)
            deduction = {"critical": 0.2, "high": 0.15, "medium": 0.1, "low": 0.05}
            score -= deduction.get(issue.severity, 0.05)

        # Hashtag style check
        hashtag_issues = self._check_hashtag_style(content, profile)
        for issue in hashtag_issues:
            result.issues.append(issue)
            score -= 0.1

        # CTA style check
        cta_issues = self._check_cta(content, profile)
        for issue in cta_issues:
            result.issues.append(issue)
            score -= 0.1

        # Sentence length check
        sentence_issues = self._check_sentence_length(content, profile)
        for issue in sentence_issues:
            result.issues.append(issue)
            score -= 0.05

        result.score = max(0.0, score)
        result.compute_status()
        self._check_count += 1
        return result

    def _check_emoji(self, content: str, profile: BrandProfile) -> List[VoiceIssue]:
        issues: List[VoiceIssue] = []
        emoji_pattern = re.compile(r'[\U0001F300-\U0010FFFF]', re.UNICODE)
        emojis = emoji_pattern.findall(content)
        emoji_count = len(emojis)
        sentences = max(1, len(re.split(r'[.!?]+', content)))

        if profile.emoji_style == "none" and emoji_count > 0:
            issues.append(VoiceIssue(
                category="emoji", severity="critical",
                description=f"Emojis found but brand uses no emojis ({emoji_count})",
                suggestion="Remove all emojis to maintain brand style",
                current_value=str(emoji_count),
                expected_value="0",
            ))
        elif profile.emoji_style == "minimal" and emoji_count > sentences * 1.5:
            issues.append(VoiceIssue(
                category="emoji", severity="medium",
                description=f"Too many emojis for minimal style ({emoji_count})",
                suggestion="Reduce emoji usage to 0-1 per sentence max",
                current_value=str(emoji_count),
                expected_value=f"<={sentences}",
            ))
        elif profile.emoji_style == "heavy" and emoji_count < sentences * 0.5:
            issues.append(VoiceIssue(
                category="emoji", severity="low",
                description="Heavy emoji style but few emojis used",
                suggestion="Add more emojis to match brand style",
            ))

        return issues

    def _check_hashtag_style(self, content: str, profile: BrandProfile) -> List[VoiceIssue]:
        issues: List[VoiceIssue] = []
        hashtags = re.findall(r'#\w+', content)

        if profile.hashtag_style == "none" and hashtags:
            issues.append(VoiceIssue(
                category="hashtag_style", severity="medium",
                description="Brand uses no hashtags but hashtags found",
                suggestion="Remove hashtags to maintain brand style",
            ))
        elif profile.hashtag_style == "branded":
            branded = [h for h in hashtags if profile.brand_name.lower() in h.lower()]
            if hashtags and not branded:
                issues.append(VoiceIssue(
                    category="hashtag_style", severity="low",
                    description="Hashtags found but no branded hashtags used",
                    suggestion=f"Add #{profile.brand_name.replace(' ', '')} or similar branded hashtag",
                ))

        min_h, max_h = profile.hashtag_count_range
        if hashtags and (len(hashtags) < min_h or len(hashtags) > max_h):
            issues.append(VoiceIssue(
                category="hashtag_style", severity="low",
                description=f"Hashtag count ({len(hashtags)}) outside brand profile range ({min_h}-{max_h})",
                suggestion=f"Use {min_h}-{max_h} hashtags per brand profile",
                current_value=str(len(hashtags)),
                expected_value=f"{min_h}-{max_h}",
            ))

        return issues

    def _check_cta(self, content: str, profile: BrandProfile) -> List[VoiceIssue]:
        issues: List[VoiceIssue] = []
        content_lower = content.lower()
        ctas = profile.preferred_ctas or CTA_PATTERNS.get(profile.cta_style, [])

        if profile.cta_style != "none" and ctas:
            found = any(cta.lower() in content_lower for cta in ctas)
            if not found:
                issues.append(VoiceIssue(
                    category="cta", severity="low",
                    description=f"No preferred {profile.cta_style} CTAs found",
                    suggestion=f"Add a call-to-action: {', '.join(ctas[:3])}",
                ))
        elif profile.cta_style == "none":
            aggressive_ctas = ["buy now", "order now", "shop now", "sign up"]
            found = any(cta in content_lower for cta in aggressive_ctas)
            if found:
                issues.append(VoiceIssue(
                    category="cta", severity="medium",
                    description="Aggressive CTA found but brand uses no CTAs",
                    suggestion="Remove direct CTAs as per brand profile",
                ))

        return issues

    def _check_sentence_length(self, content: str, profile: BrandProfile) -> List[VoiceIssue]:
        issues: List[VoiceIssue] = []
        sentences = [s.strip() for s in re.split(r'[.!?]+', content) if s.strip()]
        if not sentences:
            return issues

        min_len, max_len = profile.sentence_length_range
        too_long = sum(1 for s in sentences if len(s.split()) > max_len)
        too_short = sum(1 for s in sentences if len(s.split()) < min_len and len(s) > 5)

        if too_long > len(sentences) * 0.3:
            issues.append(VoiceIssue(
                category="sentence_length", severity="medium",
                description=f"{too_long} sentences exceed brand max ({max_len} words)",
                suggestion=f"Break long sentences into shorter ones (max {max_len} words)",
                current_value=f"{too_long} long sentences",
                expected_value=f"<={len(sentences) * 0.3}",
            ))
        if too_short > len(sentences) * 0.4:
            issues.append(VoiceIssue(
                category="sentence_length", severity="low",
                description=f"{too_short} very short sentences may affect readability",
                suggestion="Combine some short sentences for better flow",
            ))

        return issues

    @property
    def check_count(self) -> int:
        return self._check_count
