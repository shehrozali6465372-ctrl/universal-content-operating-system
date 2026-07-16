"""Clarity Analyzer — Measure content clarity and coherence."""
from __future__ import annotations
from typing import Any, Dict, List

FILLER_WORDS = {"um", "uh", "like", "basically", "actually", "literally", "very", "really", "just", "quite", "rather", "somewhat", "perhaps", "maybe"}
WEAK_WORDS = {"thing", "stuff", "things", "got", "get", "gets", "gotting", "nice", "good", "bad", "big", "small"}


class ClarityResult:
    """Clarity analysis result."""
    __slots__ = ("clarity_score", "filler_count", "weak_word_count",
                 "passive_voice_detected", "avg_paragraph_length",
                 "transition_score", "issues", "suggestions")

    def __init__(self) -> None:
        self.clarity_score = 0.0
        self.filler_count = 0
        self.weak_word_count = 0
        self.passive_voice_detected = False
        self.avg_paragraph_length = 0.0
        self.transition_score = 0.0
        self.issues: List[str] = []
        self.suggestions: List[str] = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "clarity_score": round(self.clarity_score, 3),
            "filler_count": self.filler_count,
            "weak_word_count": self.weak_word_count,
            "passive_voice_detected": self.passive_voice_detected,
            "avg_paragraph_length": round(self.avg_paragraph_length, 1),
            "transition_score": round(self.transition_score, 3),
            "issues": self.issues,
        }


class ClarityAnalyzer:
    """Analyzes content clarity and coherence."""

    def __init__(self) -> None:
        self._analysis_count = 0

    def analyze(self, text: str) -> ClarityResult:
        """Analyze text clarity."""
        result = ClarityResult()
        words = text.lower().split()
        word_count = max(len(words), 1)

        # Filler words
        result.filler_count = sum(1 for w in words if w.strip(".,!?;:") in FILLER_WORDS)
        if result.filler_count > 0:
            result.issues.append(f"Found {result.filler_count} filler words")
            result.suggestions.append("Remove filler words for clearer writing")

        # Weak words
        result.weak_word_count = sum(1 for w in words if w.strip(".,!?;:") in WEAK_WORDS)
        if result.weak_word_count > 2:
            result.issues.append(f"Found {result.weak_word_count} weak/generic words")
            result.suggestions.append("Replace weak words with specific alternatives")

        # Passive voice (simplified)
        passive_patterns = ["was", "were", "been", "being", "is", "are", "am"]
        result.passive_voice_detected = any(w in passive_patterns for w in words)

        # Paragraph structure
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        if paragraphs:
            result.avg_paragraph_length = sum(len(p.split()) for p in paragraphs) / len(paragraphs)
            if result.avg_paragraph_length > 100:
                result.issues.append("Paragraphs too long — break into smaller chunks")

        # Transition words
        transitions = {"however", "therefore", "moreover", "furthermore", "additionally", "consequently", "meanwhile", "finally", "first", "second", "third"}
        transition_count = sum(1 for w in words if w in transitions)
        result.transition_score = min(transition_count / max(len(paragraphs), 1), 1.0)

        # Overall score
        score = 100.0
        score -= result.filler_count * 5
        score -= result.weak_word_count * 3
        score -= max(0, result.avg_paragraph_length - 80) * 0.5
        result.clarity_score = max(0, min(score, 100)) / 100

        self._analysis_count += 1
        return result

    @property
    def analysis_count(self) -> int:
        return self._analysis_count
