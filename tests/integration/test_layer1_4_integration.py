"""Layer 1-4 Integration Sprint — End-to-end: Topic → Research → Intelligence → Writing → Multi-platform."""
import time
from layers.layer03_intelligence.modules.content_understanding.content_analyzer import ContentAnalyzer
from layers.layer03_intelligence.modules.trend_intelligence.trend_predictor import TrendPredictor
from layers.layer03_intelligence.modules.content_intelligence.quality_estimator import QualityEstimator
from layers.layer03_intelligence.modules.knowledge_fusion.fusion_engine import FusionEngine
from layers.layer03_intelligence.modules.strategy_engine.strategy_manager import StrategyManager
from layers.layer03_intelligence.modules.intelligence_memory.intel_memory_manager import IntelMemoryManager
from layers.layer04_writing.modules.content_planner.planner_manager import PlannerManager
from layers.layer04_writing.modules.draft_generator.draft_manager import DraftManager
from layers.layer04_writing.modules.draft_generator.llm_provider import MockLLMProvider
from layers.layer04_writing.modules.writing_orchestrator.writing_orchestrator import WritingOrchestrator


class TestLayer1to4Integration:
    """Full pipeline: Topic → Research signals → Intelligence → Writing → Multi-platform."""

    def setup_method(self):
        self.content_analyzer = ContentAnalyzer()
        self.trend_predictor = TrendPredictor()
        self.quality_estimator = QualityEstimator()
        self.fusion_engine = FusionEngine()
        self.strategy_manager = StrategyManager()
        self.memory = IntelMemoryManager()
        self.planner = PlannerManager()
        self.draft_manager = DraftManager(provider=MockLLMProvider(
            response="AI developers are in high demand in 2026. Companies worldwide are investing heavily in artificial intelligence talent. The average salary has increased by 30%. This trend is expected to continue as more businesses adopt AI solutions."
        ))
        self.orchestrator = WritingOrchestrator()

    def test_end_to_end_topic_to_multiplatform(self):
        topic = "AI Career Roadmap 2026"
        text = "AI developers are in high demand. Salaries increased 30%."
        history = [30, 45, 60, 75, 90]

        ca = self.content_analyzer.analyze(text, "general")
        prediction = self.trend_predictor.predict(topic, history)
        quality = self.quality_estimator.estimate(text)
        ui = self.fusion_engine.fuse(topic, {"trend": {"score": prediction.confidence}, "quality": {"score": quality.overall_score}})
        strat = self.strategy_manager.run_pipeline(topic, score=85.0, intent="educate", trend_data={"momentum": 0.8, "confidence": prediction.confidence}, content_data={"quality_score": quality.overall_score})
        self.memory.remember("pipeline_test", {"topic": topic, "trend": prediction.predicted_direction, "quality": quality.overall_score}, confidence=0.88, tags=["pipeline", "e2e"])
        plan_result = self.planner.create_plan(topic=topic, user_goal="educate", intelligence_data={"intent": "educate", "expected_engagement": 0.7}, audience_hint="students")
        draft_result = self.draft_manager.generate(plan_result.plan)
        multi_platform = self.orchestrator.run(topic=topic, platforms=["facebook", "instagram", "twitter", "linkedin"], goal="educate", audience="students")

        assert prediction.confidence > 0
        assert quality.overall_score > 0
        assert ui.confidence > 0
        assert strat.selected_strategy is not None
        assert plan_result.plan is not None
        assert plan_result.validation.is_valid
        assert draft_result.draft is not None
        assert len(multi_platform.outputs) == 4
        for o in multi_platform.outputs:
            assert len(o.caption) > 0
            assert o.cta != ""

    def test_confidence_propagation(self):
        quality = self.quality_estimator.estimate("Crypto markets recovering.")
        prediction = self.trend_predictor.predict("Crypto", [20, 30, 45, 60, 70])
        strat = self.strategy_manager.run_pipeline("Crypto", score=70, content_data={"quality_score": quality.overall_score})
        plan = self.planner.create_plan("Crypto", user_goal="educate")
        draft = self.draft_manager.generate(plan.plan)
        assert quality.overall_score > 0
        assert prediction.confidence > 0
        assert strat.selected_strategy.confidence > 0
        assert draft.draft is not None

    def test_pipeline_with_strategy_goals(self):
        strat = self.strategy_manager.run_pipeline("Health Tech", score=80, intent="inspire", goal_configs=[{"name": "Publish guide", "priority": "high"}])
        plan = self.planner.create_plan("Health Tech", user_goal="inspire", audience_hint="entrepreneurs")
        multi = self.orchestrator.run(topic="Health Tech", platforms=["facebook", "linkedin"], goal="inspire", audience="entrepreneurs")
        assert len(multi.outputs) == 2
        for o in multi.outputs:
            assert o.hook != ""
            assert o.cta != ""

    def test_pipeline_performance(self):
        start = time.time()
        result = self.orchestrator.run("Python Tutorial", platforms=["facebook", "instagram", "twitter", "linkedin"], goal="educate", audience="students")
        elapsed = (time.time() - start) * 1000
        assert elapsed < 10000
        assert result.pipeline_time_ms > 0

    def test_pipeline_memory_across_runs(self):
        self.orchestrator.run("Topic A", platforms=["facebook"])
        self.orchestrator.run("Topic B", platforms=["twitter"])
        assert len(self.orchestrator.get_history(platform="facebook")) >= 1
        assert len(self.orchestrator.get_history(platform="twitter")) >= 1

    def test_pipeline_variants(self):
        plan = self.planner.create_plan("AI Jobs", user_goal="educate")
        variants = self.draft_manager.generate_variants(plan.plan, variant_types=["original", "bold", "minimal"])
        assert len(variants.variants) == 3

    def test_full_data_flow(self):
        topic = "Digital Marketing"
        quality = self.quality_estimator.estimate("Digital marketing strategies for 2026.")
        prediction = self.trend_predictor.predict(topic, [30, 40, 55, 70, 85])
        plan = self.planner.create_plan(topic, user_goal="educate", intelligence_data={"intent": "educate"})
        assert plan.plan.goal == "educate"
        assert plan.plan.topic == topic
        draft = self.draft_manager.generate(plan.plan)
        assert draft.draft.text != ""
        multi = self.orchestrator.run(topic, platforms=["facebook", "instagram"])
        assert len(multi.outputs) == 2
