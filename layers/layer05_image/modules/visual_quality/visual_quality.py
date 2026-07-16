"""Visual Quality Scorer — Evaluate image plan quality."""
from __future__ import annotations
from typing import Any, Dict, List


class QualityScore:
    __slots__ = ("composition_score", "text_density_score", "safe_margins",
                 "clickability", "overall_score", "issues", "grade")

    def __init__(self) -> None:
        self.composition_score = 0.5
        self.text_density_score = 0.5
        self.safe_margins = 0.5
        self.clickability = 0.5
        self.overall_score = 0.0
        self.issues: List[str] = []
        self.grade = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "composition": round(self.composition_score, 3),
            "text_density": round(self.text_density_score, 3),
            "safe_margins": round(self.safe_margins, 3),
            "clickability": round(self.clickability, 3),
            "overall_score": round(self.overall_score, 3),
            "grade": self.grade,
            "issues": self.issues,
        }


class VisualQualityScorer:
    GRADES = [(0.9, "A+"), (0.8, "A"), (0.7, "B+"), (0.6, "B"), (0.5, "C+"), (0.4, "C"), (0.0, "D")]

    def __init__(self) -> None:
        self._score_count = 0

    def score(self, image_type: str = "photo", text_overlay: str = "",
              has_face: bool = False, has_logo: bool = False,
              platform: str = "facebook") -> QualityScore:
        result = QualityScore()

        if image_type in ("photo", "illustration"):
            result.composition_score = 0.8
        elif image_type in ("infographic", "carousel"):
            result.composition_score = 0.7
        else:
            result.composition_score = 0.6
        if has_face:
            result.composition_score += 0.1

        words = text_overlay.split() if text_overlay else []
        if len(words) <= 5:
            result.text_density_score = 0.9
        elif len(words) <= 10:
            result.text_density_score = 0.7
        else:
            result.text_density_score = 0.4
            result.issues.append("Text overlay too dense")

        result.safe_margins = 0.8

        if image_type == "meme":
            result.clickability = 0.85
        elif image_type == "thumbnail":
            result.clickability = 0.8
        elif has_face:
            result.clickability = 0.75
        else:
            result.clickability = 0.6

        if platform in ("instagram", "pinterest") and image_type in ("photo", "infographic"):
            result.clickability += 0.05

        weights = [0.3, 0.2, 0.2, 0.3]
        scores = [result.composition_score, result.text_density_score,
                  result.safe_margins, result.clickability]
        result.overall_score = round(sum(s * w for s, w in zip(scores, weights)), 3)

        for threshold, grade in self.GRADES:
            if result.overall_score >= threshold:
                result.grade = grade
                break

        self._score_count += 1
        return result

    @property
    def score_count(self) -> int:
        return self._score_count
