"""Variant Generator — Generate A/B test variants of drafts."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional

from layers.layer04_writing.modules.content_planner.writing_plan import WritingPlan
from layers.layer04_writing.modules.draft_generator.prompt_builder import PromptBuilder


VARIANT_TYPES = {
    "original": "The original version as planned.",
    "alternative": "A different style and approach.",
    "bold": "More provocative and attention-grabbing.",
    "minimal": "Shorter and punchier.",
    "detailed": "More detailed with examples and explanations.",
    "emotional": "More emotionally engaging with storytelling.",
    "question_hook": "Starts with a compelling question.",
    "stat_hook": "Opens with a surprising statistic.",
}


class DraftVariant:
    """A single draft variant."""
    __slots__ = ("variant_id", "variant_type", "prompt_set", "draft_text",
                 "score", "metadata", "created_at")

    def __init__(self, variant_type: str = "original") -> None:
        self.variant_id = f"var_{int(time.time() * 1000) % 10000000}"
        self.variant_type = variant_type
        self.prompt_set = None
        self.draft_text = ""
        self.score = 0.0
        self.metadata: Dict[str, Any] = {}
        self.created_at = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "variant_id": self.variant_id,
            "variant_type": self.variant_type,
            "has_draft": bool(self.draft_text),
            "score": round(self.score, 3),
        }


class VariantGenerator:
    """Generates A/B test variants of content plans."""

    def __init__(self, prompt_builder: Optional[PromptBuilder] = None) -> None:
        self.prompt_builder = prompt_builder or PromptBuilder()
        self._generation_count = 0

    def generate_variants(
        self,
        plan: WritingPlan,
        variant_types: Optional[List[str]] = None,
    ) -> List[DraftVariant]:
        """Generate multiple variants from a plan."""
        types = variant_types or ["original", "alternative", "bold"]
        variants: List[DraftVariant] = []

        for vt in types:
            v = DraftVariant(variant_type=vt)
            v.prompt_set = self.prompt_builder.build_variant(plan, variant_type=vt)
            v.metadata = {"description": VARIANT_TYPES.get(vt, "")}
            variants.append(v)

        self._generation_count += 1
        return variants

    def score_variants(self, variants: List[DraftVariant]) -> List[DraftVariant]:
        """Score variants based on quality signals."""
        for v in variants:
            score = 50.0
            if v.draft_text:
                word_count = len(v.draft_text.split())
                if 50 < word_count < 500:
                    score += 10
                if v.draft_text[0].isupper():
                    score += 5
                if v.draft_text.rstrip().endswith(('!', '?')):
                    score += 5
                if '?' in v.draft_text:
                    score += 5
            v.score = min(score, 100.0)
        return sorted(variants, key=lambda v: v.score, reverse=True)

    @property
    def generation_count(self) -> int:
        return self._generation_count
