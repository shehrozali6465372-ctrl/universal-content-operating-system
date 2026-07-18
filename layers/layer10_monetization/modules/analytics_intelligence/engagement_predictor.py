"""EngagementPredictor — Predict content engagement before publishing."""
from __future__ import annotations
import itertools
import time
from typing import Any, Dict, List, Optional

_EP_COUNTER = itertools.count(1)


class EngagementPrediction:
    """A prediction of content engagement."""

    __slots__ = ("prediction_id", "topic", "platform", "predicted_likes",
                 "predicted_comments", "predicted_shares", "predicted_ctr",
                 "predicted_reach", "virality_score", "confidence",
                 "predicted_at", "actual_likes", "actual_comments",
                 "actual_shares", "accuracy")

    def __init__(self, topic: str = "", platform: str = "") -> None:
        self.prediction_id: str = f"ep_{next(_EP_COUNTER)}"
        self.topic = topic
        self.platform = platform
        self.predicted_likes: int = 0
        self.predicted_comments: int = 0
        self.predicted_shares: int = 0
        self.predicted_ctr: float = 0.0
        self.predicted_reach: int = 0
        self.virality_score: float = 0.0
        self.confidence: float = 0.5
        self.predicted_at: float = time.time()
        self.actual_likes: Optional[int] = None
        self.actual_comments: Optional[int] = None
        self.actual_shares: Optional[int] = None
        self.accuracy: Optional[float] = None

    def record_actual(self, likes: Optional[int] = None,
                      comments: Optional[int] = None,
                      shares: Optional[int] = None) -> None:
        self.actual_likes = likes
        self.actual_comments = comments
        self.actual_shares = shares
        if self.predicted_likes > 0 and likes is not None:
            self.accuracy = min(1.0, 1.0 - abs(likes - self.predicted_likes) / max(1, likes))

    def to_dict(self) -> Dict[str, Any]:
        return {"prediction_id": self.prediction_id, "topic": self.topic,
                "platform": self.platform,
                "predicted_likes": self.predicted_likes,
                "confidence": round(self.confidence, 3)}


class EngagementPredictor:
    """Predict engagement for content before publishing."""

    def __init__(self) -> None:
        self._predictions: List[EngagementPrediction] = []
        self._base_rates: Dict[str, float] = {
            "facebook": 0.03, "instagram": 0.05, "x": 0.02,
            "linkedin": 0.04, "youtube": 0.06, "tiktok": 0.08,
            "reddit": 0.03, "medium": 0.02,
        }

    def predict(self, topic: str, platform: str,
                historical_engagement: float = 0.0) -> EngagementPrediction:
        pred = EngagementPrediction(topic, platform)
        base = self._base_rates.get(platform, 0.03)
        multiplier = 1.0 + historical_engagement
        pred.predicted_likes = int(base * multiplier * 100)
        pred.predicted_comments = int(base * multiplier * 20)
        pred.predicted_shares = int(base * multiplier * 10)
        pred.predicted_ctr = min(1.0, base * multiplier * 2)
        pred.predicted_reach = int(base * multiplier * 1000)
        pred.virality_score = min(1.0, base * multiplier * 3)
        pred.confidence = min(0.95, 0.3 + base * multiplier)
        self._predictions.append(pred)
        return pred

    def predict_batch(self, items: List[Dict[str, str]]) -> List[EngagementPrediction]:
        results = []
        for item in items:
            topic = item.get("topic", "untitled")
            platform = item.get("platform", "universal")
            h = item.get("historical_engagement", 0.0)
            if not isinstance(h, (int, float)):
                h = 0.0
            results.append(self.predict(topic, platform, float(h)))
        return results

    def set_base_rate(self, platform: str, rate: float) -> None:
        self._base_rates[platform] = rate

    def get_base_rates(self) -> Dict[str, float]:
        return dict(self._base_rates)

    def get_predictions(self, platform: str = "") -> List[EngagementPrediction]:
        if platform:
            return [p for p in self._predictions if p.platform == platform]
        return list(self._predictions)

    def get_avg_accuracy(self) -> float:
        accuracies = [p.accuracy for p in self._predictions if p.accuracy is not None]
        if not accuracies:
            return 0.0
        return round(sum(accuracies) / len(accuracies), 3)

    def get_stats(self) -> Dict[str, Any]:
        return {"total_predictions": len(self._predictions),
                "avg_confidence": round(
                    sum(p.confidence for p in self._predictions) / max(1, len(self._predictions)), 3),
                "avg_accuracy": self.get_avg_accuracy()}
