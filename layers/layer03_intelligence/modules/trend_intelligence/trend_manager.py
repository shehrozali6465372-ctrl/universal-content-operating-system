"""Trend Manager - Orchestrator for Trend Intelligence Module."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional

from layers.layer03_intelligence.modules.trend_intelligence.trend_collector import TrendCollector
from layers.layer03_intelligence.modules.trend_intelligence.trend_normalizer import TrendNormalizer
from layers.layer03_intelligence.modules.trend_intelligence.momentum_analyzer import MomentumAnalyzer
from layers.layer03_intelligence.modules.trend_intelligence.lifecycle_detector import LifecycleDetector
from layers.layer03_intelligence.modules.trend_intelligence.seasonality_analyzer import SeasonalityAnalyzer
from layers.layer03_intelligence.modules.trend_intelligence.virality_predictor import ViralityPredictor
from layers.layer03_intelligence.modules.trend_intelligence.cross_platform_fusion import CrossPlatformFusion
from layers.layer03_intelligence.modules.trend_intelligence.trend_confidence import TrendConfidence
from layers.layer03_intelligence.modules.trend_intelligence.trend_explainer import TrendExplainer


class TrendAnalysisResult:
    """Complete trend analysis result combining all sub-modules."""
    __slots__ = ("topic", "normalized", "momentum", "lifecycle", "seasonality",
                 "virality", "cross_platform", "confidence", "explanation",
                 "recommendation", "timestamp")

    def __init__(self, topic: str = "") -> None:
        self.topic = topic
        self.normalized: Optional[Any] = None
        self.momentum: Optional[Any] = None
        self.lifecycle: Optional[Any] = None
        self.seasonality: Optional[Any] = None
        self.virality: Optional[Any] = None
        self.cross_platform: Optional[Any] = None
        self.confidence: Optional[Any] = None
        self.explanation: Optional[Any] = None
        self.recommendation = ""
        self.timestamp = time.time()

    def to_dict(self) -> Dict:
        return {
            "topic": self.topic,
            "normalized": self.normalized.to_dict() if self.normalized else None,
            "momentum": self.momentum.to_dict() if self.momentum else None,
            "lifecycle": self.lifecycle.to_dict() if self.lifecycle else None,
            "seasonality": self.seasonality.to_dict() if self.seasonality else None,
            "virality": self.virality.to_dict() if self.virality else None,
            "cross_platform": self.cross_platform.to_dict() if self.cross_platform else None,
            "confidence": self.confidence.to_dict() if self.confidence else None,
            "explanation": self.explanation.to_dict() if self.explanation else None,
            "recommendation": self.recommendation,
            "timestamp": self.timestamp,
        }


class TrendManager:
    """Main orchestrator for trend intelligence analysis."""

    def __init__(self) -> None:
        self.collector = TrendCollector()
        self.normalizer = TrendNormalizer()
        self.momentum = MomentumAnalyzer()
        self.lifecycle = LifecycleDetector()
        self.seasonality = SeasonalityAnalyzer()
        self.virality = ViralityPredictor()
        self.cross_platform = CrossPlatformFusion()
        self.confidence = TrendConfidence()
        self.explainer = TrendExplainer()

    def analyze_topic(self, topic: str, data: Dict) -> TrendAnalysisResult:
        """Run full trend analysis pipeline for a topic."""
        result = TrendAnalysisResult(topic)

        scores = data.get("scores", [])
        if scores:
            result.normalized = self.normalizer.normalize(topic, scores)

        momentum_data = data.get("momentum_data", [])
        if momentum_data:
            result.momentum = self.momentum.analyze(momentum_data)

        lifecycle_data = data.get("lifecycle_data", momentum_data)
        if lifecycle_data:
            result.lifecycle = self.lifecycle.detect(lifecycle_data)

        time_series = data.get("time_series", [])
        if time_series:
            result.seasonality = self.seasonality.detect(topic, time_series)

        virality_data = data.get("virality_data", {})
        if virality_data:
            result.virality = self.virality.predict(topic, virality_data)

        platform_data = data.get("platform_data", {})
        if platform_data:
            result.cross_platform = self.cross_platform.fuse(topic, platform_data)

        confidence_signals = {
            "data_points": len(scores) or len(momentum_data),
            "source_count": len(platform_data) or len(scores),
            "hours_since_latest": data.get("hours_since_latest", 24),
            "score_variance": data.get("score_variance", 0.2),
        }
        result.confidence = self.confidence.calculate(topic, confidence_signals)

        analysis_for_explainer = {
            "momentum": result.momentum.to_dict() if result.momentum else {},
            "lifecycle": result.lifecycle.to_dict() if result.lifecycle else {},
            "platforms": result.cross_platform.to_dict() if result.cross_platform else {},
            "virality": result.virality.to_dict() if result.virality else {},
            "confidence": result.confidence.to_dict() if result.confidence else {},
            "competition": data.get("competition", {}),
        }
        result.explanation = self.explainer.explain(topic, analysis_for_explainer)
        result.recommendation = result.explanation.recommendation

        return result

    def analyze_batch(self, topics: List[Dict]) -> List[TrendAnalysisResult]:
        return [self.analyze_topic(t.get("topic", ""), t) for t in topics]

    def rank_topics(self, results: List[TrendAnalysisResult]) -> List[TrendAnalysisResult]:
        def _score(r: TrendAnalysisResult) -> float:
            conf = r.confidence.overall_confidence if r.confidence else 0.0
            fused = r.cross_platform.fused_score if r.cross_platform else 0.0
            return conf * 0.6 + fused * 0.4
        return sorted(results, key=_score, reverse=True)

    def get_health(self) -> Dict:
        return {
            "modules": [
                "TrendCollector", "TrendNormalizer", "MomentumAnalyzer",
                "LifecycleDetector", "SeasonalityAnalyzer", "ViralityPredictor",
                "CrossPlatformFusion", "TrendConfidence", "TrendExplainer",
            ],
            "status": "healthy",
            "entries_collected": self.collector.count(),
        }
