"""PromptAnalyzer — analyze prompt characteristics and quality."""
from __future__ import annotations

import re
from typing import Any, Dict


class PromptAnalyzer:
    """Analyze prompt characteristics, complexity, and quality."""

    def __init__(self) -> None:
        self._analysis_cache: Dict[str, Dict[str, Any]] = {}

    def analyze(self, prompt: str) -> Dict[str, Any]:
        if prompt in self._analysis_cache:
            return self._analysis_cache[prompt]

        words = prompt.split()
        sentences = re.split(r'[.!?]+', prompt)
        sentences = [s.strip() for s in sentences if s.strip()]
        questions = prompt.count("?")
        exclamations = prompt.count("!")

        # Complexity score based on word length, sentence count, vocabulary
        avg_word_len = sum(len(w) for w in words) / max(len(words), 1)
        vocabulary = len(set(w.lower() for w in words)) / max(len(words), 1)
        complexity = (avg_word_len / 10 + len(sentences) / 10 + vocabulary) / 3

        result = {
            "word_count": len(words),
            "char_count": len(prompt),
            "sentence_count": len(sentences),
            "question_count": questions,
            "exclamation_count": exclamations,
            "avg_word_length": round(avg_word_len, 2),
            "vocabulary_richness": round(vocabulary, 4),
            "complexity_score": round(complexity, 4),
            "has_variables": bool(re.search(r"\{\w+\}", prompt)),
            "has_instructions": any(w in prompt.lower() for w in ["instruction", "you must", "always", "never"]),
            "estimated_tokens": max(int(len(words) * 1.3), 1),
        }
        self._analysis_cache[prompt] = result
        return result

    def compare(self, prompt_a: str, prompt_b: str) -> Dict[str, Any]:
        a = self.analyze(prompt_a)
        b = self.analyze(prompt_b)
        return {
            "prompt_a": a, "prompt_b": b,
            "length_diff": a["word_count"] - b["word_count"],
            "complexity_diff": a["complexity_score"] - b["complexity_score"],
        }
