"""Quality Estimator — estimates content quality based on multiple signals."""
from typing import Dict, Optional

class QualityResult:
    __slots__ = ("score", "factors", "grade")
    def __init__(self):
        self.score = 0.0
        self.factors: Dict[str, float] = {}
        self.grade = "C"
    def to_dict(self) -> dict:
        return {"score": self.score, "factors": dict(self.factors), "grade": self.grade}

class QualityEstimator:
    def __init__(self, thresholds: Optional[Dict[str, float]] = None):
        self._thresholds = thresholds or {"min_length": 50, "ideal_length": 300, "max_length": 2000}
    def estimate(self, text: str, metadata: Optional[Dict] = None) -> QualityResult:
        result = QualityResult()
        meta = metadata or {}
        length = len(text)
        result.factors["length"] = min(1.0, length / self._thresholds["ideal_length"])
        words = text.split()
        result.factors["word_count"] = min(1.0, len(words) / 100)
        result.factors["has_hashtags"] = 1.0 if any(w.startswith("#") for w in words) else 0.0
        result.factors["has_question"] = 1.0 if "?" in text else 0.0
        result.factors["readability"] = min(1.0, len(set(words)) / max(len(words), 1))
        weights = {"length": 0.2, "word_count": 0.2, "has_hashtags": 0.2, "has_question": 0.15, "readability": 0.25}
        result.score = round(sum(result.factors.get(f, 0) * w for f, w in weights.items()), 3)
        if result.score >= 0.8: result.grade = "A"
        elif result.score >= 0.6: result.grade = "B"
        elif result.score >= 0.4: result.grade = "C"
        elif result.score >= 0.2: result.grade = "D"
        else: result.grade = "F"
        return result
