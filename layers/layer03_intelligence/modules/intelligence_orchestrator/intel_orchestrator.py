"""Intelligence Orchestrator — coordinates all Layer 3 modules with events, metrics, health monitoring."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional

from layers.layer03_intelligence.modules.content_understanding.content_analyzer import ContentAnalyzer
from layers.layer03_intelligence.modules.trend_intelligence.trend_predictor import TrendPredictor
from layers.layer03_intelligence.modules.trend_intelligence.momentum_analyzer import MomentumAnalyzer
from layers.layer03_intelligence.modules.trend_intelligence.lifecycle_detector import LifecycleDetector
from layers.layer03_intelligence.modules.reasoning_engine.decision_engine import DecisionEngine
from layers.layer03_intelligence.modules.reasoning_engine.strategy_selector import StrategySelector
from layers.layer03_intelligence.modules.content_intelligence.quality_estimator import QualityEstimator
from layers.layer03_intelligence.modules.content_intelligence.virality_predictor import ContentViralityPredictor
from layers.layer03_intelligence.modules.recommendation_engine.recommendation_engine import RecommendationEngine
from layers.layer03_intelligence.modules.knowledge_fusion.fusion_engine import FusionEngine
from layers.layer03_intelligence.modules.strategy_engine.strategy_engine import StrategyEngine
from layers.layer03_intelligence.modules.intelligence_memory.intel_cache import IntelligenceCache


class PipelineEvent:
    """An event emitted during pipeline execution."""
    __slots__ = ("event_type", "module", "data", "timestamp", "duration_ms")

    def __init__(self, event_type: str = "", module: str = "") -> None:
        self.event_type = event_type
        self.module = module
        self.data: Dict[str, Any] = {}
        self.timestamp = time.time()
        self.duration_ms = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.event_type,
            "module": self.module,
            "duration_ms": round(self.duration_ms, 2),
            "timestamp": self.timestamp,
        }


class ModuleMetrics:
    """Metrics for a single module execution."""
    __slots__ = ("module_name", "execution_count", "total_time_ms",
                 "success_count", "failure_count")

    def __init__(self, module_name: str = "") -> None:
        self.module_name = module_name
        self.execution_count = 0
        self.total_time_ms = 0.0
        self.success_count = 0
        self.failure_count = 0

    @property
    def avg_time_ms(self) -> float:
        return round(self.total_time_ms / max(self.execution_count, 1), 2)

    @property
    def success_rate(self) -> float:
        return round(self.success_count / max(self.execution_count, 1), 3)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "module": self.module_name,
            "executions": self.execution_count,
            "avg_time_ms": self.avg_time_ms,
            "success_rate": self.success_rate,
        }


class HealthStatus:
    """Health status of the orchestrator."""
    __slots__ = ("status", "module_health", "issues", "last_check")

    def __init__(self) -> None:
        self.status = "healthy"
        self.module_health: Dict[str, str] = {}
        self.issues: List[str] = []
        self.last_check = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "module_health": self.module_health,
            "issues": self.issues,
            "last_check": self.last_check,
        }


class IntelligenceResult:
    """Complete intelligence output for a topic."""
    __slots__ = ("topic", "content_understanding", "trend_prediction", "momentum",
                 "lifecycle", "quality", "virality", "strategy", "recommendations",
                 "overall_confidence", "processing_time_ms", "events", "metadata")

    def __init__(self, topic: str = "") -> None:
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
        self.events: List[PipelineEvent] = []
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "topic": self.topic,
            "content_understanding": self.content_understanding.to_dict() if self.content_understanding else None,
            "trend_prediction": self.trend_prediction.to_dict() if self.trend_prediction else None,
            "momentum": self.momentum.to_dict() if self.momentum else None,
            "lifecycle": self.lifecycle.to_dict() if self.lifecycle else None,
            "quality": self.quality.to_dict() if self.quality else None,
            "virality": self.virality.to_dict() if self.virality else None,
            "strategy": self.strategy.to_dict() if self.strategy else None,
            "overall_confidence": round(self.overall_confidence, 3),
            "processing_time_ms": round(self.processing_time_ms, 2),
            "event_count": len(self.events),
        }


class IntelligenceOrchestrator:
    """Full intelligence pipeline with events, metrics, and health monitoring.

    Pipeline: understand → predict → reason → recommend → return
    """

    def __init__(self) -> None:
        self.content_analyzer = ContentAnalyzer()
        self.trend_predictor = TrendPredictor()
        self.momentum_analyzer = MomentumAnalyzer()
        self.lifecycle_detector = LifecycleDetector()
        self.decision_engine = DecisionEngine()
        self.strategy_selector = StrategySelector()
        self.quality_estimator = QualityEstimator()
        self.virality_predictor = ContentViralityPredictor()
        self.recommendation_engine = RecommendationEngine()
        self.fusion_engine = FusionEngine()
        self.strategy_engine = StrategyEngine()
        self.cache = IntelligenceCache()
        self._metrics: Dict[str, ModuleMetrics] = {}
        self._health = HealthStatus()
        self._total_analyses = 0
        self._total_events = 0

    def analyze(
        self,
        topic: str,
        text: str = "",
        trend_history: Optional[List[float]] = None,
        domain: str = "general",
    ) -> IntelligenceResult:
        """Run full intelligence analysis on a topic."""
        start = time.time()
        result = IntelligenceResult(topic)

        # Cache check
        cache_key = f"intel_{topic}_{domain}"
        cached = self.cache.get(cache_key)
        if cached:
            cached.metadata["cached"] = True
            return cached

        history = trend_history or [50.0]

        # 1. Content Understanding
        if text:
            result.content_understanding = self._run_module(
                "content_understanding", lambda: self.content_analyzer.analyze(text, domain)
            )

        # 2. Trend Intelligence
        result.trend_prediction = self._run_module(
            "trend_prediction", lambda: self.trend_predictor.predict(topic, history)
        )
        result.momentum = self._run_module(
            "momentum", lambda: self.momentum_analyzer.analyze(history)
        )
        result.lifecycle = self._run_module(
            "lifecycle", lambda: self.lifecycle_detector.detect(history)
        )

        # 3. Quality & Virality
        if text:
            result.quality = self._run_module(
                "quality", lambda: self.quality_estimator.estimate(text)
            )
            result.virality = self._run_module(
                "virality", lambda: self.virality_predictor.predict(text)
            )

        # 4. Strategy Selection
        result.strategy = self._run_module(
            "strategy", lambda: self.strategy_selector.select({})
        )

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
            confidences.append(result.quality.overall_score)
        result.overall_confidence = round(sum(confidences) / max(len(confidences), 1), 3)

        # Timing
        elapsed = (time.time() - start) * 1000
        result.processing_time_ms = elapsed
        result.events = list(self._last_events)
        result.metadata = {"cached": False, "domain": domain}

        # Cache
        self.cache.store(cache_key, result)
        self._total_analyses += 1
        return result

    def analyze_batch(
        self, topics: List[Dict[str, Any]], domain: str = "general"
    ) -> List[IntelligenceResult]:
        """Analyze multiple topics."""
        results: List[IntelligenceResult] = []
        for t in topics:
            name = t.get("topic", t.get("title", ""))
            text = t.get("text", "")
            history = t.get("history", [50.0])
            results.append(self.analyze(name, text, history, domain))
        return results

    def _run_module(self, name: str, fn: Any) -> Any:
        """Run a module function with metrics and event tracking."""
        self._last_events: List[PipelineEvent] = []
        event = PipelineEvent(event_type="module_start", module=name)
        start = time.time()

        metrics = self._metrics.setdefault(name, ModuleMetrics(name))
        metrics.execution_count += 1

        try:
            result = fn()
            event.duration_ms = (time.time() - start) * 1000
            event.event_type = "module_complete"
            event.data = {"success": True}
            metrics.total_time_ms += event.duration_ms
            metrics.success_count += 1
            self._last_events.append(event)
            self._total_events += 1
            return result
        except Exception as e:
            event.duration_ms = (time.time() - start) * 1000
            event.event_type = "module_error"
            event.data = {"error": str(e)}
            metrics.failure_count += 1
            self._last_events.append(event)
            self._total_events += 1
            return None

    def get_metrics(self) -> Dict[str, Any]:
        """Get execution metrics for all modules."""
        return {
            name: m.to_dict() for name, m in self._metrics.items()
        }

    def get_health(self) -> HealthStatus:
        """Check health of all modules."""
        self._health = HealthStatus()
        for name, m in self._metrics.items():
            if m.execution_count > 0 and m.success_rate < 0.5:
                self._health.module_health[name] = "degraded"
                self._health.issues.append(f"{name}: low success rate ({m.success_rate:.0%})")
            else:
                self._health.module_health[name] = "healthy"
        if self._health.issues:
            self._health.status = "degraded"
        self._health.last_check = time.time()
        return self._health

    @property
    def total_analyses(self) -> int:
        return self._total_analyses

    @property
    def total_events(self) -> int:
        return self._total_events
