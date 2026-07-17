"""Content Analyzer — Analyze content strengths, weaknesses, and optimization potential."""
from __future__ import annotations
from typing import Any, Dict, List


class ContentAnalysis:
    """Analysis result for a piece of content."""

    __slots__ = ("content_id", "word_count", "sentence_count", "paragraph_count",
                 "readability_score", "engagement_potential", "seo_score",
                 "hook_strength", "cta_strength", "tone_consistency",
                 "strengths", "weaknesses", "overall_score")

    def __init__(self, content_id: str = "") -> None:
        self.content_id = content_id
        self.word_count: int = 0
        self.sentence_count: int = 0
        self.paragraph_count: int = 0
        self.readability_score: float = 0.0
        self.engagement_potential: float = 0.0
        self.seo_score: float = 0.0
        self.hook_strength: float = 0.0
        self.cta_strength: float = 0.0
        self.tone_consistency: float = 0.0
        self.strengths: List[str] = []
        self.weaknesses: List[str] = []
        self.overall_score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "content_id": self.content_id,
            "word_count": self.word_count,
            "readability_score": round(self.readability_score, 3),
            "engagement_potential": round(self.engagement_potential, 3),
            "seo_score": round(self.seo_score, 3),
            "hook_strength": round(self.hook_strength, 3),
            "cta_strength": round(self.cta_strength, 3),
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "overall_score": round(self.overall_score, 3),
        }


class ContentAnalyzer:
    """Analyze content for optimization opportunities."""

    def __init__(self) -> None:
        self._analyses: List[ContentAnalysis] = []

    def analyze(self, content: str, content_id: str = "",
                platform: str = "") -> ContentAnalysis:
        result = ContentAnalysis(content_id or f"ca_{len(self._analyses) + 1}")
        if not content or not content.strip():
            self._analyses.append(result)
            return result
        result.word_count = len(content.split())
        result.sentence_count = max(1, content.count(".") + content.count("!") + content.count("?"))
        result.paragraph_count = max(1, content.count("\n\n") + 1)
        result.readability_score = self._score_readability(content)
        result.engagement_potential = self._score_engagement(content)
        result.seo_score = self._score_seo(content)
        result.hook_strength = self._score_hook(content)
        result.cta_strength = self._score_cta(content)
        result.strengths = self._find_strengths(content, result)
        result.weaknesses = self._find_weaknesses(content, result)
        result.overall_score = round(
            result.readability_score * 0.2 + result.engagement_potential * 0.25 +
            result.seo_score * 0.15 + result.hook_strength * 0.2 +
            result.cta_strength * 0.2, 3,
        )
        self._analyses.append(result)
        return result

    def _score_readability(self, content: str) -> float:
        words = content.split()
        if not words:
            return 0.0
        avg_word_len = sum(len(w) for w in words) / len(words)
        sentences = max(1, content.count(".") + content.count("!") + content.count("?"))
        avg_sent_len = len(words) / sentences
        score = 1.0
        if avg_word_len > 6:
            score -= 0.15
        if avg_sent_len > 20:
            score -= 0.2
        elif avg_sent_len < 5:
            score -= 0.1
        return round(max(0.0, min(1.0, score)), 3)

    def _score_engagement(self, content: str) -> float:
        score = 0.3
        lower = content.lower()
        hooks = ["did you know", "here's the thing", "imagine", "what if", "discover"]
        score += min(0.3, sum(0.1 for h in hooks if h in lower))
        questions = content.count("?")
        score += min(0.2, questions * 0.05)
        emojis = sum(1 for c in content if ord(c) > 0x1F600)
        score += min(0.2, emojis * 0.05)
        return round(min(1.0, score), 3)

    def _score_seo(self, content: str) -> float:
        score = 0.4
        words = content.split()
        if words:
            unique_ratio = len(set(w.lower() for w in words)) / len(words)
            score += unique_ratio * 0.3
        hashtags = content.count("#")
        score += min(0.2, hashtags * 0.05)
        if len(content) > 300:
            score += 0.1
        return round(min(1.0, score), 3)

    def _score_hook(self, content: str) -> float:
        first_line = content.split("\n")[0] if "\n" in content else content[:100]
        score = 0.3
        if first_line.endswith("?") or first_line.endswith("!"):
            score += 0.3
        lower = first_line.lower()
        power_words = ["secret", "proven", "ultimate", "free", "exclusive", "now"]
        score += min(0.2, sum(0.1 for w in power_words if w in lower))
        if len(first_line.split()) >= 3:
            score += 0.2
        return round(min(1.0, score), 3)

    def _score_cta(self, content: str) -> float:
        lower = content.lower()
        ctas = ["comment", "share", "follow", "subscribe", "click", "join",
                "learn more", "sign up", "get started", "try now"]
        score = 0.2
        score += min(0.5, sum(0.1 for c in ctas if c in lower))
        if any(w in lower for w in ["?", "!"]):
            score += 0.2
        return round(min(1.0, score), 3)

    def _find_strengths(self, content: str, analysis: ContentAnalysis) -> List[str]:
        strengths = []
        if analysis.readability_score > 0.7:
            strengths.append("Good readability")
        if analysis.hook_strength > 0.6:
            strengths.append("Strong opening hook")
        if analysis.cta_strength > 0.6:
            strengths.append("Effective CTA")
        if analysis.engagement_potential > 0.6:
            strengths.append("High engagement potential")
        if analysis.seo_score > 0.6:
            strengths.append("Good SEO elements")
        return strengths

    def _find_weaknesses(self, content: str, analysis: ContentAnalysis) -> List[str]:
        weaknesses = []
        if analysis.readability_score < 0.5:
            weaknesses.append("Low readability — simplify language")
        if analysis.hook_strength < 0.4:
            weaknesses.append("Weak opening — add a hook")
        if analysis.cta_strength < 0.4:
            weaknesses.append("Missing or weak CTA")
        if analysis.word_count < 50:
            weaknesses.append("Content too short")
        if analysis.engagement_potential < 0.4:
            weaknesses.append("Low engagement potential — add interactive elements")
        return weaknesses

    def get_analyses(self) -> List[ContentAnalysis]:
        return list(self._analyses)
