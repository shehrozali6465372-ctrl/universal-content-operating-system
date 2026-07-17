"""Voice Analyzer — Analyze brand voice from content samples."""
from __future__ import annotations
import itertools
from typing import Any, Dict, List

_VAR_COUNTER = itertools.count(1)


class VoiceAnalysisResult:
    """Result of analyzing voice from content."""

    __slots__ = ("result_id", "detected_tones", "detected_vocabulary",
                 "formality_estimate", "emoji_density", "avg_sentence_length",
                 "avg_paragraph_length", "score", "findings")

    def __init__(self) -> None:
        self.result_id: str = f"var_{next(_VAR_COUNTER)}"
        self.detected_tones: Dict[str, float] = {}
        self.detected_vocabulary: Dict[str, float] = {}
        self.formality_estimate: str = "medium"
        self.emoji_density: float = 0.0
        self.avg_sentence_length: float = 0.0
        self.avg_paragraph_length: float = 0.0
        self.score: float = 0.0
        self.findings: List[str] = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "result_id": self.result_id,
            "detected_tones": self.detected_tones,
            "formality_estimate": self.formality_estimate,
            "emoji_density": round(self.emoji_density, 3),
            "avg_sentence_length": round(self.avg_sentence_length, 1),
            "score": round(self.score, 3),
            "finding_count": len(self.findings),
        }


class VoiceAnalyzer:
    """Analyze brand voice characteristics from content samples."""

    def __init__(self) -> None:
        self._results: List[VoiceAnalysisResult] = []

    def analyze(self, content: str, platform: str = "") -> VoiceAnalysisResult:
        result = VoiceAnalysisResult()
        result.detected_tones = self._detect_tones(content)
        result.formality_estimate = self._estimate_formality(content)
        result.emoji_density = self._calculate_emoji_density(content)
        result.avg_sentence_length = self._avg_sentence_length(content)
        result.avg_paragraph_length = self._avg_paragraph_length(content)
        result.findings = self._generate_findings(result)
        result.score = self._compute_score(result)
        self._results.append(result)
        return result

    def _detect_tones(self, content: str) -> Dict[str, float]:
        tones: Dict[str, float] = {}
        lower = content.lower()
        tone_keywords = {
            "professional": ["expert", "industry", "solution", "strategy", "enterprise"],
            "friendly": ["hello", "thanks", "awesome", "great", "love"],
            "educational": ["learn", "discover", "tip", "guide", "how to"],
            "urgent": ["now", "today", "limited", "hurry", "don't miss"],
            "inspirational": ["inspire", "dream", "achieve", "success", "growth"],
            "casual": ["hey", "btw", "lol", "totally", "vibe"],
        }
        for tone, keywords in tone_keywords.items():
            count = sum(1 for kw in keywords if kw in lower)
            if count > 0:
                tones[tone] = round(min(1.0, count / len(keywords)), 3)
        return tones

    def _estimate_formality(self, content: str) -> str:
        lower = content.lower()
        formal_indicators = ["furthermore", "therefore", "consequently", "moreover", "regarding"]
        informal_indicators = ["hey", "gonna", "wanna", "lol", "omg", "tbh", "btw"]
        formal_count = sum(1 for w in formal_indicators if w in lower)
        informal_count = sum(1 for w in informal_indicators if w in lower)
        if formal_count > informal_count:
            return "high"
        elif informal_count > formal_count:
            return "low"
        return "medium"

    def _calculate_emoji_density(self, content: str) -> float:
        if not content:
            return 0.0
        emoji_count = sum(1 for c in content if ord(c) > 0x1F600)
        return round(min(1.0, emoji_count / max(1, len(content))), 4)

    def _avg_sentence_length(self, content: str) -> float:
        sentences = [s.strip() for s in content.replace("!", ".").replace("?", ".").split(".") if s.strip()]
        if not sentences:
            return 0.0
        words_per = [len(s.split()) for s in sentences]
        return round(sum(words_per) / len(words_per), 1)

    def _avg_paragraph_length(self, content: str) -> float:
        paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
        if not paragraphs:
            paragraphs = [content]
        words_per = [len(p.split()) for p in paragraphs]
        return round(sum(words_per) / len(words_per), 1)

    def _generate_findings(self, result: VoiceAnalysisResult) -> List[str]:
        findings = []
        if result.emoji_density > 0.05:
            findings.append("High emoji density detected")
        if result.avg_sentence_length > 25:
            findings.append("Long average sentence length")
        if result.avg_sentence_length < 5 and result.avg_sentence_length > 0:
            findings.append("Very short average sentence length")
        if not result.detected_tones:
            findings.append("No clear tone detected")
        return findings

    def _compute_score(self, result: VoiceAnalysisResult) -> float:
        score = 50.0
        if result.detected_tones:
            score += min(25.0, len(result.detected_tones) * 5)
        if 0.001 < result.emoji_density < 0.03:
            score += 10
        if 8 <= result.avg_sentence_length <= 20:
            score += 15
        return min(100.0, score)

    def get_results(self) -> List[VoiceAnalysisResult]:
        return list(self._results)
