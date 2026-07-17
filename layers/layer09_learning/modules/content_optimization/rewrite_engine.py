"""Rewrite Engine — Produce optimized content variants."""
from __future__ import annotations
import itertools
from typing import Any, Dict, List

_RE_COUNTER = itertools.count(1)


class RewriteVariant:
    """An optimized variant of the original content."""

    __slots__ = ("variant_id", "content", "changes_made", "original_hash",
                 "quality_score", "applied_suggestions")

    def __init__(self, content: str = "") -> None:
        self.variant_id: str = f"rwv_{next(_RE_COUNTER)}"
        self.content = content
        self.changes_made: int = 0
        self.original_hash: str = ""
        self.quality_score: float = 0.0
        self.applied_suggestions: List[str] = []

    @property
    def word_count(self) -> int:
        return len(self.content.split()) if self.content else 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "variant_id": self.variant_id,
            "content": self.content,
            "changes_made": self.changes_made,
            "word_count": self.word_count,
            "quality_score": round(self.quality_score, 3),
            "applied_suggestions": self.applied_suggestions,
        }


class RewriteEngine:
    """Produce optimized content variants by applying suggestions."""

    def __init__(self) -> None:
        self._variants: List[RewriteVariant] = []

    def rewrite(self, original: str, suggestions: List[Dict[str, Any]],
                preserve_meaning: bool = True) -> RewriteVariant:
        variant = RewriteVariant(original)
        variant.original_hash = str(hash(original))
        changes = 0
        content = original
        for s in suggestions:
            field = s.get("field", "")
            if field == "cta" and "cta" not in content.lower():
                content = content.rstrip() + "\n\n" + s.get("suggested_value", "Share your thoughts!")
                changes += 1
                variant.applied_suggestions.append(s.get("description", "Added CTA"))
            elif field == "title":
                suggested = s.get("suggested_value", "")
                if suggested:
                    lines = content.split("\n")
                    if lines:
                        lines[0] = suggested
                        content = "\n".join(lines)
                        changes += 1
                        variant.applied_suggestions.append("Optimized title")
            elif field == "seo":
                hashtag_suggestions = ["#content", "#digitalmarketing", "#tips"]
                existing_hashtags = [w for w in content.split() if w.startswith("#")]
                if len(existing_hashtags) < 3:
                    content = content.rstrip() + "\n\n" + " ".join(hashtag_suggestions[:3])
                    changes += 1
                    variant.applied_suggestions.append("Added hashtags")
            elif field == "body":
                content = self._improve_body(content, s)
                changes += 1
                variant.applied_suggestions.append(s.get("description", "Improved body"))
        variant.content = content
        variant.changes_made = changes
        self._variants.append(variant)
        return variant

    def _improve_body(self, content: str, suggestion: Dict[str, Any]) -> str:
        desc = suggestion.get("description", "").lower()
        if "paragraph" in desc:
            lines = content.split("\n")
            improved = []
            for line in lines:
                improved.append(line)
                if len(line.split()) > 15:
                    improved.append("")
            return "\n".join(improved)
        return content

    def generate_variants(self, original: str, suggestions: List[Dict[str, Any]],
                          count: int = 3) -> List[RewriteVariant]:
        variants = []
        for i in range(min(count, len(suggestions) + 1)):
            subset = suggestions[:i + 1] if i < len(suggestions) else suggestions
            variant = self.rewrite(original, subset)
            variants.append(variant)
        return variants

    def get_variants(self) -> List[RewriteVariant]:
        return list(self._variants)
