"""Prompt Evaluator — Evaluate and refine image prompts."""
from __future__ import annotations
from typing import Any, Dict, List


class PromptEvaluation:
    __slots__ = ("prompt", "clarity_score", "specificity_score",
                 "style_coverage", "issues", "refined_prompt", "score")

    def __init__(self, prompt: str = "") -> None:
        self.prompt = prompt
        self.clarity_score = 0.5
        self.specificity_score = 0.5
        self.style_coverage = 0.5
        self.issues: List[str] = []
        self.refined_prompt = prompt
        self.score = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "clarity": round(self.clarity_score, 3),
            "specificity": round(self.specificity_score, 3),
            "style_coverage": round(self.style_coverage, 3),
            "issues": self.issues,
            "score": round(self.score, 3),
        }


class PromptEvaluator:
    QUALITY_WORDS = {"high", "detailed", "professional", "quality", "sharp", "clear", "vibrant", "realistic"}
    STYLE_WORDS = {"modern", "minimalist", "bold", "elegant", "artistic", "photorealistic"}

    def __init__(self) -> None:
        self._eval_count = 0

    def evaluate(self, prompt: str) -> PromptEvaluation:
        result = PromptEvaluation(prompt=prompt)
        words = set(prompt.lower().split())

        if len(prompt.split()) >= 5:
            result.clarity_score = 0.8
        else:
            result.clarity_score = 0.4
            result.issues.append("Prompt too short")

        quality_hits = len(words & self.QUALITY_WORDS)
        result.specificity_score = min(0.3 + quality_hits * 0.15, 1.0)
        if quality_hits == 0:
            result.issues.append("Add quality descriptors")

        style_hits = len(words & self.STYLE_WORDS)
        result.style_coverage = min(0.3 + style_hits * 0.2, 1.0)

        result.score = round(
            result.clarity_score * 0.3 + result.specificity_score * 0.4 + result.style_coverage * 0.3, 3
        )
        result.refined_prompt = self._refine(prompt, result)
        self._eval_count += 1
        return result

    def _refine(self, prompt: str, ev: PromptEvaluation) -> str:
        refined = prompt
        if ev.clarity_score < 0.6:
            refined = f"A clear, well-composed image: {refined}"
        if ev.specificity_score < 0.6:
            refined += ", high quality, detailed, professional"
        return refined

    @property
    def eval_count(self) -> int:
        return self._eval_count
