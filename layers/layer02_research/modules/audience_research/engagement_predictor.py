"""
Engagement Predictor
Layer 2: Research Engine — Module 4

Predicts engagement for content based on audience data:
- Predict engagement rate by content type
- Predict optimal posting time
- Predict topic engagement potential
- Predict format performance
- A/B test recommendation
- Confidence-weighted scoring
"""

from typing import Dict, List, Optional
from layers.layer02_research.modules.audience_research.audience_profile import AudienceProfile


class Prediction:
    """A single engagement prediction."""

    __slots__ = (
        "content_type", "topic", "predicted_engagement",
        "confidence", "best_hour", "best_day",
        "reasoning", "factors",
    )

    def __init__(
        self,
        content_type: str = "text",
        topic: str = "general",
        predicted_engagement: float = 5.0,
        confidence: float = 0.5,
        best_hour: int = 12,
        best_day: str = "Wednesday",
        reasoning: Optional[List[str]] = None,
        factors: Optional[Dict[str, float]] = None,
    ):
        self.content_type = content_type
        self.topic = topic
        self.predicted_engagement = max(0.0, min(10.0, predicted_engagement))
        self.confidence = max(0.0, min(1.0, confidence))
        self.best_hour = best_hour
        self.best_day = best_day
        self.reasoning = reasoning or []
        self.factors = factors or {}

    def to_dict(self) -> dict:
        return {
            "content_type": self.content_type,
            "topic": self.topic,
            "predicted_engagement": self.predicted_engagement,
            "confidence": self.confidence,
            "best_hour": self.best_hour,
            "best_day": self.best_day,
            "reasoning": self.reasoning,
            "factors": self.factors,
        }


class EngagementPredictor:
    """Predict engagement for content targeting specific audience segments."""

    # Base engagement rates by content type
    BASE_RATES: Dict[str, float] = {
        "video": 6.5, "reel": 7.0, "carousel": 5.5,
        "image": 4.5, "text": 3.0, "live": 8.0,
        "story": 5.0, "poll": 6.0, "infographic": 4.0,
    }

    # Multipliers by buying stage
    STAGE_MULTIPLIERS: Dict[str, float] = {
        "awareness": 0.8, "consideration": 1.0,
        "decision": 1.2, "retention": 1.1, "advocacy": 1.3, "unknown": 1.0,
    }

    def __init__(self):
        self._predictions: Dict[str, List[Prediction]] = {}

    def predict(
        self,
        audience: AudienceProfile,
        content_type: str = "text",
        topic: str = "general",
        posting_hour: int = 12,
        posting_day: str = "Wednesday",
    ) -> Prediction:
        """Predict engagement for a specific content piece."""
        base = self.BASE_RATES.get(content_type, 3.0)

        # Factor 1: Audience engagement rate
        audience_factor = (audience.engagement_rate / 10.0) if audience.engagement_rate > 0 else 1.0
        audience_factor = max(0.5, min(2.0, audience_factor))

        # Factor 2: Interest match
        interest_match = any(
            topic.lower() in i.lower() or i.lower() in topic.lower()
            for i in audience.interests
        )
        interest_factor = 1.3 if interest_match else 0.8

        # Factor 3: Time alignment
        time_factor = 1.0
        if posting_hour in audience.peak_engagement_hours:
            time_factor = 1.25

        # Factor 4: Buying stage
        stage_factor = self.STAGE_MULTIPLIERS.get(audience.buying_stage, 1.0)

        # Factor 5: Size bonus
        size_factor = 1.0
        tier = audience.get_size_tier()
        if tier in ("massive", "large"):
            size_factor = 1.1
        elif tier in ("niche",):
            size_factor = 0.9

        predicted = round(
            min(10.0, base * audience_factor * interest_factor * time_factor * stage_factor * size_factor),
            2,
        )

        # Reasoning
        reasoning = []
        if interest_match:
            reasoning.append(f"Topic '{topic}' matches audience interests")
        if posting_hour in audience.peak_engagement_hours:
            reasoning.append(f"Posting at {posting_hour}:00 aligns with peak hours")
        if audience.buying_stage in ("decision", "advocacy"):
            reasoning.append(f"Audience in '{audience.buying_stage}' stage — high intent")

        # Factors breakdown
        factors = {
            "base_rate": base,
            "audience_factor": audience_factor,
            "interest_factor": interest_factor,
            "time_factor": time_factor,
            "stage_factor": stage_factor,
            "size_factor": size_factor,
        }

        confidence = min(1.0, (audience.confidence * 0.6 + (0.2 if interest_match else 0) + 0.2))

        pred = Prediction(
            content_type=content_type, topic=topic,
            predicted_engagement=predicted, confidence=confidence,
            best_hour=posting_hour, best_day=posting_day,
            reasoning=reasoning, factors=factors,
        )

        # Store
        key = f"{audience.profile_id}"
        if key not in self._predictions:
            self._predictions[key] = []
        self._predictions[key].append(pred)

        return pred

    def predict_batch(
        self,
        audience: AudienceProfile,
        content_variants: List[Dict],
    ) -> List[Prediction]:
        """Predict engagement for multiple content variants."""
        results = []
        for variant in content_variants:
            pred = self.predict(
                audience=audience,
                content_type=variant.get("content_type", "text"),
                topic=variant.get("topic", "general"),
                posting_hour=variant.get("posting_hour", 12),
                posting_day=variant.get("posting_day", "Wednesday"),
            )
            results.append(pred)
        return sorted(results, key=lambda p: p.predicted_engagement, reverse=True)

    def recommend_ab_test(
        self,
        audience: AudienceProfile,
        topic: str = "general",
    ) -> Dict[str, any]:
        """Recommend A/B test variants."""
        variants = []
        for content_type in ["video", "carousel", "text", "image"]:
            pred = self.predict(audience, content_type=content_type, topic=topic)
            variants.append(pred.to_dict())
        variants.sort(key=lambda v: v["predicted_engagement"], reverse=True)

        return {
            "topic": topic,
            "best_variant": variants[0] if variants else None,
            "runner_up": variants[1] if len(variants) > 1 else None,
            "all_variants": variants,
            "recommendation": (
                f"Test '{variants[0]['content_type']}' vs '{variants[1]['content_type']}'"
                if len(variants) > 1 else "Need more variants"
            ),
        }

    def get_predictions(self, profile_id: str) -> List[Prediction]:
        return list(self._predictions.get(profile_id, []))

    def get_top_predictions(self, profile_id: str, count: int = 5) -> List[Prediction]:
        preds = self._predictions.get(profile_id, [])
        return sorted(preds, key=lambda p: p.predicted_engagement, reverse=True)[:count]
