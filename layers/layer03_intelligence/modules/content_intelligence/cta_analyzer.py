"""CTA Analyzer - Analyzes call-to-action effectiveness."""
from __future__ import annotations
from typing import Dict, List


class CTAResult:
    __slots__ = ("has_cta", "cta_text", "cta_type", "cta_score", "suggestions")

    def __init__(self) -> None:
        self.has_cta = False
        self.cta_text = ""
        self.cta_type = ""
        self.cta_score = 0.0
        self.suggestions: List[str] = []

    def to_dict(self) -> Dict:
        return {"has_cta": self.has_cta, "cta_text": self.cta_text,
                "cta_type": self.cta_type, "cta_score": round(self.cta_score, 3),
                "suggestions": list(self.suggestions)}


_CTA_KEYWORDS = {
    "engagement": {"like", "share", "comment", "tell", "vote", "react"},
    "traffic": {"click", "visit", "check", "link", "website", "learn more"},
    "conversion": {"buy", "subscribe", "sign up", "join", "register", "download"},
    "community": {"follow", "join", "subscribe", "community", "group"},
}


class CTAAnalyzer:
    def analyze(self, content: str) -> CTAResult:
        result = CTAResult()
        content_lower = content.lower()
        sentences = [s.strip() for s in content.split(".") if s.strip()]
        last_sentences = sentences[-3:] if len(sentences) >= 3 else sentences

        for sent in last_sentences:
            words = set(sent.lower().split())
            for cta_type, keywords in _CTA_KEYWORDS.items():
                matches = words & keywords
                if matches:
                    result.has_cta = True
                    result.cta_text = sent
                    result.cta_type = cta_type
                    result.cta_score = min(1.0, len(matches) / 2.0 + 0.3)
                    break
            if result.has_cta:
                break

        if not result.has_cta:
            result.suggestions.append("Add a clear call-to-action at the end")
            result.cta_score = 0.0
        elif result.cta_score < 0.5:
            result.suggestions.append("Strengthen the CTA with more action words")
        return result
