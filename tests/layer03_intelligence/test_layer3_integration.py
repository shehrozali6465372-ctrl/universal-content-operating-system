"""Layer 3 Integration Sprint — End-to-end intelligence pipeline tests."""
import time
from layers.layer03_intelligence.modules.content_understanding.content_analyzer import ContentAnalyzer
from layers.layer03_intelligence.modules.trend_intelligence.trend_predictor import TrendPredictor
from layers.layer03_intelligence.modules.content_intelligence.quality_estimator import QualityEstimator
from layers.layer03_intelligence.modules.recommendation_engine.recommendation_engine import RecommendationEngine
from layers.layer03_intelligence.modules.learning_signals.signal_collector import SignalCollector
from layers.layer03_intelligence.modules.knowledge_fusion.fusion_engine import FusionEngine
from layers.layer03_intelligence.modules.strategy_engine.strategy_manager import StrategyManager
from layers.layer03_intelligence.modules.intelligence_memory.intel_memory_manager import IntelMemoryManager
from layers.layer03_intelligence.modules.intelligence_orchestrator.intel_orchestrator import IntelligenceOrchestrator


class TestLayer3EndToEndPipeline:
    """Test the full Layer 3 pipeline from content understanding to strategy."""

    def setup_method(self):
        self.content = ContentAnalyzer()
        self.trend = TrendPredictor()
        self.quality = QualityEstimator()
        self.recommendation_engine = RecommendationEngine()
        self.signal = SignalCollector()
        self.fusion = FusionEngine()
        self.strategy = StrategyManager()
        self.memory = IntelMemoryManager()
        self.orchestrator = IntelligenceOrchestrator()

    def test_full_pipeline_topic_analysis(self):
        """Topic → Content → Trend → Quality → Strategy → Memory."""
        text = "AI jobs are booming in 2026. Companies need developers."

        # 1. Content Understanding
        ca = self.content.analyze(text, "general")
        assert ca is not None

        # 2. Trend Intelligence
        history = [20, 35, 50, 65, 80]
        prediction = self.trend.predict("AI Jobs", history)
        assert prediction.predicted_direction == "rising"
        assert prediction.confidence > 0

        # 3. Quality Estimation
        quality = self.quality.estimate(text)
        assert quality.overall_score > 0

        # 4. Strategy
        strat_result = self.strategy.run_pipeline(
            "AI Jobs", score=85.0, intent="educational",
            trend_data={"momentum": 0.8, "confidence": 0.9},
            audience_data={"expected_engagement": 0.7},
            content_data={"quality_score": quality.overall_score},
        )
        assert strat_result.selected_strategy is not None
        assert strat_result.explanation is not None

        # 5. Memory
        self.memory.remember("topic_analysis", {
            "topic": "AI Jobs",
            "trend": prediction.predicted_direction,
        }, confidence=0.85, tags=["AI", "jobs"])
        stats = self.memory.get_stats()
        assert stats["store"]["total"] >= 1

    def test_intelligence_layer_events_flow(self):
        """Verify events flow through the pipeline."""
        result = self.orchestrator.analyze(
            "AI Technology",
            text="Artificial Intelligence is transforming every industry rapidly.",
            trend_history=[30, 45, 60, 75, 90],
        )
        assert result.topic == "AI Technology"
        assert len(result.events) > 0
        assert result.processing_time_ms > 0
        assert result.overall_confidence > 0

    def test_confidence_propagation(self):
        """Confidence should propagate correctly through modules."""
        text = "Crypto markets are volatile but growing."

        quality = self.quality.estimate(text)

        strat = self.strategy.run_pipeline(
            "Crypto", score=65.0, intent="educational",
            content_data={"quality_score": quality.overall_score},
        )
        assert strat.selected_strategy.confidence > 0
        assert strat.explanation is not None

    def test_cross_module_data_fusion(self):
        """Test that knowledge from multiple modules can be fused."""
        self.signal.add("trend", "engagement", 0.85)
        self.signal.add("content", "quality", 0.72)
        self.signal.add("audience", "fit", 0.91)

        ui = self.fusion.fuse("AI Jobs", {
            "trend": {"score": 0.85},
            "content": {"score": 0.72},
            "audience": {"score": 0.91},
        })
        assert ui.topic == "AI Jobs"
        assert ui.confidence > 0

    def test_memory_pattern_learning(self):
        """Test that patterns can be learned and retrieved."""
        self.memory.learn_pattern("topic", "AI posts get high engagement", confidence=0.9)
        self.memory.learn_pattern("timing", "Evening posts perform better", confidence=0.8)

        self.memory.store_case("AI", "post_guide", outcome="success", score=0.9)
        self.memory.store_case("AI", "post_news", outcome="failure", score=0.3)

        cases = self.memory.find_similar_cases("AI")
        assert len(cases) >= 1

    def test_orchestrator_batch_analysis(self):
        """Test batch analysis through orchestrator."""
        topics = [
            {"topic": "AI", "text": "AI is growing", "history": [20, 40, 60, 80]},
            {"topic": "Crypto", "text": "Bitcoin surges", "history": [50, 40, 60, 70]},
            {"topic": "Health", "text": "Fitness trends", "history": [30, 40, 50, 60]},
        ]
        results = self.orchestrator.analyze_batch(topics)
        assert len(results) == 3
        for r in results:
            assert r.topic != ""
            assert r.processing_time_ms > 0

    def test_orchestrator_metrics_tracking(self):
        """Verify metrics are tracked across analyses."""
        self.orchestrator.analyze("AI", text="test")
        self.orchestrator.analyze("Crypto", text="test2")

        metrics = self.orchestrator.get_metrics()
        assert len(metrics) > 0

        health = self.orchestrator.get_health()
        assert health.status in ("healthy", "degraded")

    def test_strategy_memory_integration(self):
        """Test strategy engine memory integration."""
        strat = self.strategy.run_pipeline("AI Jobs", score=85.0, intent="educational")
        stats = self.strategy.get_memory_stats()
        assert stats["total"] >= 1

        self.strategy.memory.store(
            strat.selected_strategy.to_dict(),
            outcome="success",
            performance_score=0.9,
            tags=["AI", "educational"],
        )

        successful = self.strategy.memory.get_successful(min_score=0.8)
        assert len(successful) >= 1

    def test_full_pipeline_timing(self):
        """Performance test: full pipeline should complete in reasonable time."""
        start = time.time()
        result = self.orchestrator.analyze(
            "AI Technology",
            text="AI is transforming industries with new capabilities every day.",
            trend_history=[20, 35, 50, 65, 80],
        )
        elapsed = (time.time() - start) * 1000
        assert elapsed < 5000
        assert result.processing_time_ms > 0

    def test_end_to_end_all_features(self):
        """Comprehensive end-to-end test with all Layer 3 features."""
        text = "AI developers are in high demand. Salaries have increased 30% in 2026."
        history = [30, 40, 55, 70, 85]

        # Content Understanding
        ca = self.content.analyze(text, "general")

        # Trend
        prediction = self.trend.predict("AI Jobs", history)

        # Quality
        quality = self.quality.estimate(text)

        # Signals
        self.signal.add("research", "trend_score", 0.85)
        self.signal.add("research", "audience_fit", 0.9)

        # Fusion
        ui = self.fusion.fuse("AI Jobs", {
            "trend": {"score": prediction.confidence},
            "quality": {"score": quality.overall_score},
        })

        # Strategy
        strat = self.strategy.run_pipeline(
            "AI Jobs",
            score=85.0,
            intent="educational",
            trend_data={"momentum": 0.8, "confidence": prediction.confidence},
            audience_data={"expected_engagement": 0.7, "confidence": 0.85},
            content_data={"quality_score": quality.overall_score},
            goal_configs=[{"name": "Publish AI guide", "priority": "high"}],
        )

        # Memory
        self.memory.remember("e2e_analysis", {
            "topic": "AI Jobs",
            "trend": prediction.predicted_direction,
            "quality": quality.overall_score,
            "confidence": ui.confidence,
            "strategy": strat.selected_strategy.name if strat.selected_strategy else "",
        }, confidence=0.88, tags=["AI", "e2e", "complete"])

        # Verify everything
        assert prediction.confidence > 0
        assert quality.overall_score > 0
        assert ui.confidence > 0
        assert strat.selected_strategy is not None
        assert strat.explanation is not None
        assert self.memory.get_stats()["store"]["total"] >= 1
