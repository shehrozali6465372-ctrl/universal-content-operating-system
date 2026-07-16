"""Rewrite Suggester — Generate rewrite suggestions for flagged content.

Suggests specific actions for flagged segments:
- Paraphrase
- Add attribution
- Remove cliché
- Diversify vocabulary
"""
from __future__ import annotations
from typing import Dict, List, Optional

from layers.layer06_quality.modules.plagiarism_originality_engine.originality_report import FlaggedSegment


# Synonym maps for common overused words
_SYNONYM_MAP: Dict[str, List[str]] = {
    "good": ["excellent", "outstanding", "remarkable", "commendable"],
    "bad": ["poor", "subpar", "inadequate", "lacking"],
    "important": ["crucial", "essential", "vital", "significant"],
    "big": ["substantial", "considerable", "extensive", "major"],
    "small": ["minor", "slight", "modest", "limited"],
    "fast": ["rapid", "swift", "quick", "accelerated"],
    "slow": ["gradual", "steady", "deliberate", "measured"],
    "new": ["novel", "innovative", "fresh", "emerging"],
    "old": ["established", "traditional", "legacy", "longstanding"],
    "show": ["demonstrate", "illustrate", "highlight", "reveal"],
    "help": ["assist", "facilitate", "support", "enable"],
    "make": ["create", "develop", "produce", "generate"],
    "get": ["obtain", "acquire", "achieve", "attain"],
    "use": ["utilize", "leverage", "employ", "apply"],
    "give": ["provide", "offer", "supply", "deliver"],
    "think": ["believe", "consider", "assess", "evaluate"],
    "very": ["extremely", "highly", "exceptionally", "remarkably"],
    "really": ["truly", "genuinely", "undoubtedly", "certainly"],
    "nice": ["pleasant", "enjoyable", "impressive", "delightful"],
}


class RewriteSuggestion:
    """A rewrite suggestion for a flagged segment."""

    __slots__ = ("original_text", "suggestion_type", "suggested_text",
                 "reason", "priority")

    def __init__(
        self,
        original_text: str = "",
        suggestion_type: str = "paraphrase",
        suggested_text: str = "",
        reason: str = "",
        priority: str = "low",
    ) -> None:
        self.original_text = original_text
        self.suggestion_type = suggestion_type
        self.suggested_text = suggested_text
        self.reason = reason
        self.priority = priority

    def to_dict(self) -> dict:
        return {
            "original_text": self.original_text[:200],
            "suggestion_type": self.suggestion_type,
            "suggested_text": self.suggested_text[:200],
            "reason": self.reason,
            "priority": self.priority,
        }


class RewriteSuggester:
    """Generate rewrite suggestions for flagged content."""

    def __init__(self) -> None:
        self._suggest_count = 0

    def suggest_for_segments(self, segments: List[FlaggedSegment]) -> List[RewriteSuggestion]:
        """Generate suggestions for all flagged segments."""
        suggestions: List[RewriteSuggestion] = []
        for seg in segments:
            suggestion = self._generate_suggestion(seg)
            if suggestion:
                suggestions.append(suggestion)
        self._suggest_count += 1
        return suggestions

    def suggest_for_cliches(self, text: str) -> List[RewriteSuggestion]:
        """Generate specific suggestions for clichés."""
        suggestions: List[RewriteSuggestion] = []
        cliches = [
            "at the end of the day", "in this day and age",
            "it goes without saying", "needless to say",
            "the fact of the matter", "to be honest",
            "in my humble opinion", "the bottom line is",
            "first and foremost", "last but not least",
            "time will tell", "easier said than done",
        ]
        for cliche in cliches:
            if cliche in text.lower():
                suggestions.append(RewriteSuggestion(
                    original_text=cliche,
                    suggestion_type="remove_cliche",
                    suggested_text=f"[Replace '{cliche}' with original phrasing]",
                    reason=f"Cliché '{cliche}' is overused and reduces originality",
                    priority="low",
                ))
        self._suggest_count += 1
        return suggestions

    def suggest_vocabulary_enhancement(self, text: str) -> List[RewriteSuggestion]:
        """Suggest vocabulary improvements for overused words."""
        suggestions: List[RewriteSuggestion] = []
        words = text.split()
        word_counts: Dict[str, int] = {}
        for w in words:
            clean = w.lower().strip(".,!?;:")
            if len(clean) > 3:
                word_counts[clean] = word_counts.get(clean, 0) + 1

        for word, count in word_counts.items():
            if count >= 3 and word in _SYNONYM_MAP:
                synonyms = _SYNONYM_MAP[word]
                suggestions.append(RewriteSuggestion(
                    original_text=f"'{word}' used {count} times",
                    suggestion_type="vocabulary_enhancement",
                    suggested_text=f"Consider alternatives: {', '.join(synonyms[:3])}",
                    reason=f"'{word}' appears {count} times — diversify vocabulary",
                    priority="low" if count < 5 else "medium",
                ))

        self._suggest_count += 1
        return suggestions

    def _generate_suggestion(self, segment: FlaggedSegment) -> Optional[RewriteSuggestion]:
        """Generate a suggestion based on segment type."""
        if segment.match_type == "exact_repeat":
            return RewriteSuggestion(
                original_text=segment.text,
                suggestion_type="paraphrase",
                suggested_text=f"[Paraphrase: rephrase '{segment.text}' with different words]",
                reason="Exact phrase repeated — rephrase for variety",
                priority=segment.severity,
            )
        if segment.match_type == "cliche":
            return RewriteSuggestion(
                original_text=segment.text,
                suggestion_type="remove_cliche",
                suggested_text="[Replace cliché with original phrasing]",
                reason=f"Cliché '{segment.text}' is overused",
                priority="low",
            )
        if segment.match_type == "ngram_repeat":
            return RewriteSuggestion(
                original_text=segment.text,
                suggestion_type="diversify",
                suggested_text=f"[Diversify: reword '{segment.text}']",
                reason=f"Repeated n-gram detected ({segment.similarity_score:.0%} similarity)",
                priority=segment.severity,
            )
        return None

    @property
    def suggest_count(self) -> int:
        return self._suggest_count
