"""PromptValidator — validate prompts for safety, quality, and structure."""
from __future__ import annotations

import re
from typing import Any, Dict, List


class PromptValidator:
    """Validate prompts for safety, quality, and structure."""

    def __init__(self) -> None:
        self._dangerous_patterns = re.compile(
            r"(ignore.*instructions|forget.*rules|bypass.*safety|"
            r"act.*as.*developer|system.*prompt|jailbreak)", re.I
        )

    def validate(self, prompt: str) -> Dict[str, Any]:
        issues: List[str] = []
        warnings: List[str] = []

        if not prompt or not prompt.strip():
            issues.append("Empty prompt")

        if len(prompt) < 10:
            warnings.append("Prompt is very short")

        if len(prompt) > 10000:
            warnings.append("Prompt is very long")

        if self._dangerous_patterns.search(prompt):
            warnings.append("Possible prompt injection pattern detected")

        if prompt.count("?") > 5:
            warnings.append("Too many questions — may confuse the model")

        if prompt.count("!") > 5:
            warnings.append("Too many exclamations — may bias output")

        return {"valid": len(issues) == 0, "issues": issues,
                "warnings": warnings, "length": len(prompt),
                "word_count": len(prompt.split())}

    def is_safe(self, prompt: str) -> bool:
        return not bool(self._dangerous_patterns.search(prompt))

    def estimate_tokens(self, prompt: str) -> int:
        words = len(prompt.split())
        chars = len(prompt)
        est = int(words * 1.3 + chars * 0.04)
        return max(est, 1)
