"""Quality Estimator - Scores content quality on multiple dimensions."""
from __future__ import annotations
from typing import Dict, List, Optional


class QualityResult:
    __slots__ = ("overall_score", "dimensions", "grade", "strengths", "weaknesses")
    def __init__(self) -> None:
        self.overall_score = 0.0
        self.dimensions: Dict[str, float] = {}
        self.grade = ""
        self.strengths: List[str] = []
        self.weaknesses: List[str] = []
    def to_dict(self) -> Dict:
        return {
            "overall_score": round(self.overall_score, 3),
            "dimensions": {k: round(v, 3) for k, v in self.dimensions.items()},
            "grade": self.grade, "strengths": list(self.strengths), "weaknesses": list(self.weaknesses),
        }


class QualityEstimator:
    def __init__(self, weights: Optional[Dict[str, float]] = None) -> None:
        self._weights = weights or {"grammar": 0.2, "clarity": 0.2, "engagement": 0.2, "relevance": 0.2, "originality": 0.2}

    def estimate(self, content: str, metadata: Optional[Dict] = None) -> QualityResult:
        result = QualityResult()
        metadata = metadata or {}
        sentences = [s.strip() for s in content.replace("!", ".").replace("?", ".").split(".") if s.strip()]
        avg_len = sum(len(s.split()) for s in sentences) / max(len(sentences), 1)
        result.dimensions["grammar"] = max(0.3, min(1.0, 1.0 - abs(avg_len - 15) / 30))
        words = content.split()
        complex_words = sum(1 for w in words if len(w) > 10)
        result.dimensions["clarity"] = max(0.3, 1.0 - complex_words / max(len(words), 1) * 3)
        engagement_signals = content.count("!") + content.count("?")
        result.dimensions["engagement"] = min(1.0, 0.3 + engagement_signals * 0.1)
        topic = metadata.get("topic", "")
        if topic:
            topic_words = set(topic.lower().split())
            content_words = set(w.lower() for w in words)
            result.dimensions["relevance"] = min(1.0, 0.3 + len(topic_words & content_words) / max(len(topic_words), 1) * 0.7)
        else:
            result.dimensions["relevance"] = 0.5
        result.dimensions["originality"] = min(1.0, len(set(w.lower() for w in words)) / max(len(words), 1) + 0.2)
        total_w = sum(self._weights.get(d, 0.2) for d in result.dimensions)
        total_s = sum(result.dimensions[d] * self._weights.get(d, 0.2) for d in result.dimensions)
        result.overall_score = total_s / total_w if total_w > 0 else 0.5
        if result.overall_score >= 0.9: result.grade = "A+"
        elif result.overall_score >= 0.8: result.grade = "A"
        elif result.overall_score >= 0.7: result.grade = "B"
        elif result.overall_score >= 0.6: result.grade = "C"
        else: result.grade = "D"
        for dim, score in result.dimensions.items():
            if score >= 0.8: result.strengths.append(dim)
            elif score < 0.5: result.weaknesses.append(dim)
        return result
