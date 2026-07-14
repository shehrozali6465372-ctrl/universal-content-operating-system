"""
Trend Predictor
Predicts future trend trajectory based on historical data.
"""

from typing import Dict, List


class TrendPrediction:
    """Prediction for a trend's future trajectory."""

    __slots__ = ("topic", "predicted_direction", "predicted_score", "confidence", "timeframe_days")

    def __init__(self, topic: str = ""):
        self.topic = topic
        self.predicted_direction = "stable"  # rising, falling, stable, peak
        self.predicted_score = 0.0
        self.confidence = 0.0
        self.timeframe_days = 7

    def to_dict(self) -> dict:
        return {
            "topic": self.topic,
            "predicted_direction": self.predicted_direction,
            "predicted_score": self.predicted_score,
            "confidence": self.confidence,
            "timeframe_days": self.timeframe_days,
        }


class TrendPredictor:
    """Predicts trend trajectory using momentum and historical patterns."""

    def predict(self, topic: str, history: List[float], timeframe_days: int = 7) -> TrendPrediction:
        """Predict trend direction based on score history."""
        pred = TrendPrediction(topic)
        pred.timeframe_days = timeframe_days

        if len(history) < 2:
            pred.predicted_direction = "stable"
            pred.predicted_score = history[0] if history else 0.0
            pred.confidence = 0.3
            return pred

        # Calculate momentum
        recent = history[-3:] if len(history) >= 3 else history
        avg_recent = sum(recent) / len(recent)
        avg_older = sum(history[:-len(recent)]) / max(len(history) - len(recent), 1) if len(history) > len(recent) else avg_recent

        momentum = avg_recent - avg_older
        current = history[-1]

        if momentum > 2.0:
            pred.predicted_direction = "rising"
            pred.predicted_score = min(100.0, current + momentum * timeframe_days * 0.3)
            pred.confidence = min(0.95, 0.5 + abs(momentum) * 0.05)
        elif momentum < -2.0:
            pred.predicted_direction = "falling"
            pred.predicted_score = max(0.0, current + momentum * timeframe_days * 0.3)
            pred.confidence = min(0.95, 0.5 + abs(momentum) * 0.05)
        elif current > 70:
            pred.predicted_direction = "peak"
            pred.predicted_score = current
            pred.confidence = 0.6
        else:
            pred.predicted_direction = "stable"
            pred.predicted_score = current
            pred.confidence = 0.7

        pred.confidence = round(pred.confidence, 3)
        pred.predicted_score = round(pred.predicted_score, 2)
        return pred

    def predict_batch(self, topics: Dict[str, List[float]], timeframe_days: int = 7) -> List[TrendPrediction]:
        """Predict trends for multiple topics."""
        return [self.predict(topic, history, timeframe_days) for topic, history in topics.items()]

    def rank_by_opportunity(self, predictions: List[TrendPrediction]) -> List[TrendPrediction]:
        """Rank predictions by opportunity (rising + high confidence)."""
        def opp_score(p: TrendPrediction) -> float:
            direction_bonus = {"rising": 3, "stable": 2, "peak": 1, "falling": 0}
            return p.predicted_score * p.confidence * direction_bonus.get(p.predicted_direction, 1)
        return sorted(predictions, key=opp_score, reverse=True)
