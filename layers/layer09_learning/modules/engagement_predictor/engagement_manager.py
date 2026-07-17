"""Engagement Manager — Full pipeline orchestrator for engagement prediction."""
from __future__ import annotations
import itertools
import time
from typing import Any, Dict, List, Optional

from layers.layer09_learning.modules.engagement_predictor.prediction_profile import PredictionProfile
from layers.layer09_learning.modules.engagement_predictor.feature_extractor import FeatureExtractor
from layers.layer09_learning.modules.engagement_predictor.engagement_model import EngagementModel
from layers.layer09_learning.modules.engagement_predictor.virality_estimator import ViralityEstimator
from layers.layer09_learning.modules.engagement_predictor.timing_optimizer import TimingOptimizer
from layers.layer09_learning.modules.engagement_predictor.audience_predictor import AudiencePredictor
from layers.layer09_learning.modules.engagement_predictor.prediction_memory import PredictionMemory
from layers.layer09_learning.modules.engagement_predictor.prediction_metrics import PredictionMetrics
from layers.layer09_learning.modules.engagement_predictor.prediction_validator import PredictionValidator

_EGMGR_COUNTER = itertools.count(1)


class EngagementReport:
    """Full engagement prediction report."""

    __slots__ = ("report_id", "prediction", "virality", "timing",
                 "audience", "validation", "duration_ms", "timestamp")

    def __init__(self) -> None:
        self.report_id: str = f"er_{next(_EGMGR_COUNTER)}"
        self.prediction = None
        self.virality = None
        self.timing = None
        self.audience = None
        self.validation = None
        self.duration_ms: float = 0.0
        self.timestamp: float = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "prediction": self.prediction.to_dict() if self.prediction else None,
            "virality": self.virality.to_dict() if self.virality else None,
            "timing": [t.to_dict() for t in self.timing] if self.timing else None,
            "audience": self.audience.to_dict() if self.audience else None,
            "validation": self.validation.to_dict() if self.validation else None,
            "duration_ms": round(self.duration_ms, 1),
        }


class EngagementManager:
    """Orchestrate the full engagement prediction pipeline.

    Flow: Extract Features → Predict Engagement → Estimate Virality
          → Optimize Timing → Predict Audience → Validate → Store → Report
    """

    def __init__(self) -> None:
        self.extractor = FeatureExtractor()
        self.model = EngagementModel()
        self.virality_estimator = ViralityEstimator()
        self.timing_optimizer = TimingOptimizer()
        self.audience_predictor = AudiencePredictor()
        self.memory = PredictionMemory()
        self.metrics = PredictionMetrics()
        self.validator = PredictionValidator(self.memory)
        self._reports: List[EngagementReport] = []
        self._events: List[Dict[str, Any]] = []

    def predict(self, content: str, profile: Optional[PredictionProfile] = None,
                audience_size: int = 0, platform: str = "") -> EngagementReport:
        start = time.time()
        report = EngagementReport()
        if profile is None:
            profile = PredictionProfile(platform=platform)
        elif platform and not profile.platform:
            profile.platform = platform

        # Step 1: Extract features
        features = self.extractor.extract(content, platform=profile.platform,
                                          content_type=profile.content_type)

        # Step 2: Predict engagement
        prediction = self.model.predict(features, platform=profile.platform,
                                        horizon=profile.horizon,
                                        audience_size=audience_size)
        report.prediction = prediction
        self.metrics.record_prediction(prediction.confidence)

        # Step 3: Virality estimation
        if profile.include_virality:
            report.virality = self.virality_estimator.estimate(prediction, profile.platform)

        # Step 4: Timing optimization
        if profile.include_timing:
            report.timing = self.timing_optimizer.predict_for_content(
                platform=profile.platform,
                content_type=profile.content_type,
            )

        # Step 5: Audience prediction
        if profile.include_audience:
            report.audience = self.audience_predictor.predict(
                prediction, platform=profile.platform, audience_size=audience_size,
            )

        # Step 6: Validate
        report.validation = self.validator.validate(prediction, profile.platform)

        # Step 7: Store in memory
        pred_dict = prediction.to_dict()
        self.memory.store(
            content_id=pred_dict.get("prediction_id", ""),
            predicted=pred_dict,
            platform=profile.platform,
            content_type=profile.content_type,
        )

        report.duration_ms = (time.time() - start) * 1000
        self._reports.append(report)
        self._events.append({
            "event": "engagement_predicted",
            "report_id": report.report_id,
            "confidence": prediction.confidence,
            "valid": report.validation.is_valid if report.validation else True,
        })
        return report

    def record_actual(self, report_id: str, actual: Dict[str, float]) -> bool:
        """Record actual outcomes for a prediction."""
        for r in self._reports:
            if r.report_id == report_id and r.prediction:
                pred_dict = r.prediction.to_dict()
                self.memory.record_actual_by_content(pred_dict.get("prediction_id", ""), actual)
                for key in ("likes", "comments", "shares", "reach"):
                    if key in pred_dict and key in actual:
                        self.metrics.record_comparison(
                            pred_dict[key], actual[key],
                            confidence=r.prediction.confidence,
                        )
                return True
        return False

    def get_health(self) -> Dict[str, Any]:
        return {
            "total_reports": len(self._reports),
            "memory_stats": self.memory.get_stats(),
            "metrics": self.metrics.get_summary(),
            "accuracy": self.memory.compute_accuracy(),
        }

    def get_recent_reports(self, count: int = 5) -> List[EngagementReport]:
        return list(self._reports[-count:])

    @property
    def events(self) -> List[Dict[str, Any]]:
        return list(self._events)

    @property
    def prediction_count(self) -> int:
        return len(self._reports)
