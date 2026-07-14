"""Intelligence Orchestrator — coordinates all Layer 3 modules."""
from typing import Dict, List, Optional

from layers.layer03_intelligence.modules.content_understanding.content_analyzer import ContentAnalyzer
from layers.layer03_intelligence.modules.trend_intelligence.trend_predictor import TrendPredictor
from layers.layer03_intelligence.modules.trend_intelligence.momentum_analyzer import MomentumAnalyzer
from layers.layer03_intelligence.modules.trend_intelligence.lifecycle_detector import LifecycleDetector
from layers.layer03_intelligence.modules.reasoning_engine.decision_engine import DecisionEngine
from layers.layer03_intelligence.modules.reasoning_engine.strategy_selector import StrategySelector
from layers.layer03_intelligence.modules.content_intelligence.quality_estimator import QualityEstimator
from layers.layer03_intelligence.modules.content_intelligence.virality_predictor import ViralityPredictor
from layers.layer03_intelligence.modules.recommendation_engine.recommendation_engine import RecommendationEngine
from layers.layer03_intelligence.modules.knowledge_fusion.fusion_engine import FusionEngine
from layers.layer03_intelligence.modules.strategy_engine.strategy_engine import StrategyEngine
from layers.layer03_intelligence.modules.intelligence_memory.intel_cache import IntelligenceCache


class IntelligenceResult:
    """Complete intelligence output for a topic."""
    __slots__ = ("topic", "content_understanding", "trend_prediction", "momentum",
                 "lifecycle", "quality", "virality", "strategy", "recommendations",
                 "overall_confidence", "processing_time_ms")

    def __init__(self, topic: str = ""):
        self.topic = topic
        self.content_understanding = None
        self.trend_prediction = None
        self.momentum = None
        self.lifecycle = None
        self.quality = None
        self.virality = None
        self.strategy = None
        self.recommendations: list = []
        self.overall_confidence = 0.0
        self.processing_time_ms = 0.0

    def to_dict(self) -> dict:
        return {
            "topic": self.topic,
            "content_understanding": self.content_understanding.to_dict() if self.content_understanding else None,
            "trend_prediction": self.trend_prediction.to_dict() if self.trend_prediction else None,
            "momentum": self.momentum.to_dict() if self.momentum else None,
            "lifecycle": self.lifecycle.to_dict() if self.lifecycle else None,
            "quality": self.quality.to_dict() if self.quality else None,
            "virality": self.virality.to_dict() if self.virality else None,
            "strategy": self.strategy.to_dict() if self.strategy else None,
            "overall_confidence": self.overall_confidence,
        }


class IntelligenceOrchestrator:
    """Full intelligence pipeline: understand → predict → reason → recommend."""

    def __init__(self):
        self.content_analyzer = ContentAnalyzer()
        self.trend_predictor = TrendPredictor()
        self.momentum_analyzer = MomentumAnalyzer()
        self.lifecycle_detector = LifecycleDetector()
        self.decision_engine = DecisionEngine()
        self.strategy_selector = StrategySelector()
        self.quality_estimator = QualityEstimator()
        self.virality_predictor = ViralityPredictor()
        self.recommendation_engine = RecommendationEngine()
        self.fusion_engine = FusionEngine()
        self.strategy_engine = StrategyEngine()
        self.cache = IntelligenceCache()

    def analyze(self, topic: str, text: str = "", trend_history: Optional[List[float]] = None,
                domain: str = "general") -> IntelligenceResult:
        """Run full intelligence analysis on a topic."""
        # Check cache
        cache_key = f"intel_{topic}_{domain}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        result = IntelligenceResult(topic)
        history = trend_history or [50.0]

        # 1. Content Understanding
        if text:
            result.content_understanding = self.content_analyzer.analyze(text, domain)

        # 2. Trend Intelligence
        result.trend_prediction = self.trend_predictor.predict(topic, history)
        result.momentum = self.momentum_analyzer.analyze(history)
        result.lifecycle = self.lifecycle_detector.detect(history)

        # 3. Quality & Virality
        if text:
            result.quality = self.quality_estimator.estimate(text)
            result.virality = self.virality_predictor.predict(text)

        # 4. Strategy Selection
        result.strategy = self.strategy_selector.select({})

        # 5. Recommendations
        self.recommendation_engine.clear()
        if result.trend_prediction:
            self.recommendation_engine.generate_topic_recommendations(
                [{"topic": topic, "overall_score": result.trend_prediction.predicted_score}]
            )
        result.recommendations = [r.to_dict() for r in self.recommendation_engine.get_top(3)]

        # 6. Overall confidence
        confidences = []
        if result.content_understanding and result.content_understanding.overall_score > 0:
            confidences.append(result.content_understanding.overall_score / 10)
        if result.trend_prediction:
            confidences.append(result.trend_prediction.confidence)
        if result.quality:
            confidences.append(result.quality.score)
        result.overall_confidence = round(sum(confidences) / max(len(confidences), 1), 3)

        # Cache result
        self.cache.store(cache_key, result)
        return result

    def analyze_batch(self, topics: List[Dict], domain: str = "general") -> List[IntelligenceResult]:
        """Analyze multiple topics."""
        results = []
        for t in topics:
            name = t.get("topic", t.get("title", ""))
            text = t.get("text", "")
            history = t.get("history", [50.0])
            results.append(self.analyze(name, text, history, domain))
        return results
