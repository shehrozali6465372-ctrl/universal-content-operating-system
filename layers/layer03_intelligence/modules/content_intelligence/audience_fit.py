"""Audience Fit Analyzer — checks content-audience alignment."""
from typing import Dict, Optional

class AudienceFitResult:
    __slots__ = ("fit_score", "match_factors", "recommendation")
    def __init__(self):
        self.fit_score = 0.0
        self.match_factors: Dict[str, float] = {}
        self.recommendation = ""
    def to_dict(self) -> dict:
        return {"fit_score": self.fit_score, "match_factors": dict(self.match_factors), "recommendation": self.recommendation}

class AudienceFitAnalyzer:
    def analyze(self, content_keywords: list, audience_interests: list, audience_demographics: Optional[Dict] = None) -> AudienceFitResult:
        result = AudienceFitResult()
        content_set = set(k.lower() for k in content_keywords)
        interest_set = set(i.lower() for i in audience_interests)
        overlap = content_set & interest_set
        result.match_factors["keyword_overlap"] = len(overlap) / max(len(content_set | interest_set), 1)
        demo = audience_demographics or {}
        result.match_factors["demographic_fit"] = 0.7 if demo else 0.5
        weights = {"keyword_overlap": 0.6, "demographic_fit": 0.4}
        result.fit_score = round(sum(result.match_factors.get(f, 0) * w for f, w in weights.items()), 3)
        if result.fit_score >= 0.7: result.recommendation = "strong_fit"
        elif result.fit_score >= 0.4: result.recommendation = "moderate_fit"
        else: result.recommendation = "weak_fit"
        return result
