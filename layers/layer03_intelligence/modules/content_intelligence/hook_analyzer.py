"""Hook Analyzer - Analyzes content opening hooks."""
from __future__ import annotations
from typing import Dict, List


class HookResult:
    __slots__ = ("hook_text", "hook_type", "hook_score", "effectiveness", "suggestions")

    def __init__(self) -> None:
        self.hook_text = ""
        self.hook_type = ""
        self.hook_score = 0.0
        self.effectiveness = ""
        self.suggestions: List[str] = []

    def to_dict(self) -> Dict:
        return {"hook_text": self.hook_text, "hook_type": self.hook_type,
                "hook_score": round(self.hook_score, 3), "effectiveness": self.effectiveness,
                "suggestions": list(self.suggestions)}


class HookAnalyzer:
    HOOK_PATTERNS = {
        "question": {"what", "how", "why", "did", "do", "can", "is", "are"},
        "statistic": set(),
        "statement": {"everyone", "nobody", "always", "never", "most"},
        "command": {"stop", "start", "never", "always", "listen", "remember"},
    }

    def analyze(self, content: str) -> HookResult:
        result = HookResult()
        first_sentence = content.split(".")[0] if "." in content else content[:100]
        result.hook_text = first_sentence.strip()
        words = set(first_sentence.lower().split())

        # Detect hook type
        for htype, markers in self.HOOK_PATTERNS.items():
            if markers and words & markers:
                result.hook_type = htype
                break
        if not result.hook_type:
            result.hook_type = "statement"

        # Score
        score = 0.4
        if "?" in first_sentence: score += 0.2
        if any(c.isdigit() for c in first_sentence): score += 0.15
        if len(first_sentence.split()) <= 15: score += 0.15
        if any(w in words for w in {"secret", "amazing", "shocking", "proven"}): score += 0.1
        result.hook_score = min(1.0, score)

        if result.hook_score >= 0.7: result.effectiveness = "strong"
        elif result.hook_score >= 0.5: result.effectiveness = "moderate"
        else: result.effectiveness = "weak"

        if result.hook_score < 0.5:
            result.suggestions.append("Add a question or statistic to the opening")
        return result
