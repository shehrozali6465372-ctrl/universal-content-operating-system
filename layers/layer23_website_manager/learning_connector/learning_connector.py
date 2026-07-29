"""LearningConnector — Final Module of Layer 23.

Self-Evolution Brain for Universal AI Content Operating System.

Collects data from all 12 modules, analyzes performance, detects mistakes,
learns strategies, optimizes prompts, makes decisions, recognizes patterns,
manages knowledge, generates recommendations, applies self-improvements,
manages versions, and connects to universal memory.

Flow:
    Modules 1-12 → LearningConnector → Self-Improvement → Universal AI OS
"""
from __future__ import annotations
import time
import threading
from typing import Any, Dict, List, Optional

from layers.layer23_website_manager.learning_connector.collector.learning_collector import (
    LearningCollector,
)
from layers.layer23_website_manager.learning_connector.analyzer.performance_analyzer import (
    PerformanceAnalyzer,
)
from layers.layer23_website_manager.learning_connector.mistakes.mistake_detector import (
    MistakeDetector,
)
from layers.layer23_website_manager.learning_connector.strategy.strategy_learner import (
    StrategyLearner,
)
from layers.layer23_website_manager.learning_connector.prompts.prompt_optimizer import (
    PromptOptimizer,
)
from layers.layer23_website_manager.learning_connector.decisions.decision_engine import (
    DecisionEngine,
)
from layers.layer23_website_manager.learning_connector.patterns.pattern_recognizer import (
    PatternRecognizer,
)
from layers.layer23_website_manager.learning_connector.knowledge.knowledge_base_manager import (
    KnowledgeBaseManager,
)
from layers.layer23_website_manager.learning_connector.recommendations.recommendation_engine import (
    RecommendationEngine,
)
from layers.layer23_website_manager.learning_connector.improvement.self_improvement_manager import (
    SelfImprovementManager,
)
from layers.layer23_website_manager.learning_connector.versions.version_manager import (
    VersionManager,
)
from layers.layer23_website_manager.learning_connector.memory.universal_memory_connector import (
    UniversalMemoryConnector,
)
from layers.layer23_website_manager.learning_connector.api.learning_api import (
    LearningAPI,
)
from layers.layer23_website_manager.learning_connector.models.learning_models import (
    LearningSummary,
)
from layers.layer23_website_manager.learning_connector.exceptions import (
    LearningError,
)

# Default knowledge entries for initial learning
_INITIAL_KNOWLEDGE = [
    ("content_best_practices",
     "High-quality, original content with proper SEO performs best.",
     "initialization", 0.8, ["content", "seo"]),
    ("publishing_frequency",
     "Consistent daily publishing yields better results than sporadic posting.",
     "initialization", 0.7, ["publishing", "strategy"]),
    ("pin_optimization",
     "Vertical images (2:3 ratio) with rich descriptions perform best on Pinterest.",
     "initialization", 0.9, ["pinterest", "pins"]),
    ("affiliate_best_practices",
     "Contextual affiliate links in high-value content convert better.",
     "initialization", 0.7, ["affiliate", "monetization"]),
    ("seo_importance",
     "SEO-optimized titles and descriptions significantly increase organic reach.",
     "initialization", 0.85, ["seo", "traffic"]),
]


class LearningConnector:
    """Self-evolution brain for Universal AI Content Operating System.

    Continuously learns from Modules 1-12 and improves system performance
    through automated analysis, pattern recognition, and self-improvement.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._start_time: float = time.time()
        self._learning_cycles: int = 0
        self._cycle_thread: Optional[threading.Thread] = None
        self._cycle_running: bool = False

        # Core components
        self.collector = LearningCollector()
        self.analyzer = PerformanceAnalyzer()
        self.mistakes = MistakeDetector()
        self.strategy = StrategyLearner()
        self.prompts = PromptOptimizer()
        self.decisions = DecisionEngine()
        self.patterns = PatternRecognizer()
        self.knowledge = KnowledgeBaseManager()
        self.recommendations = RecommendationEngine()
        self.improvements = SelfImprovementManager()
        self.versions = VersionManager()
        self.memory = UniversalMemoryConnector()

        # API
        self.api = LearningAPI(self)

        # Initialize default knowledge
        self._init_knowledge()
        # Initialize decision rules
        self._init_decision_rules()
        # Register default improvement handlers
        self._init_improvement_handlers()

    def _init_knowledge(self) -> None:
        for topic, content, source, confidence, tags in _INITIAL_KNOWLEDGE:
            self.knowledge.add_entry(topic, content, source, confidence, tags)

    def _init_decision_rules(self) -> None:
        rules = [
            ("generate more pins", "increase_pin_production",
             0.6, "Low pin count detected, increase production"),
            ("publish faster", "accelerate_publishing",
             0.5, "Reduce publishing interval"),
            ("change strategy", "rethink_strategy",
             0.4, "Current strategy underperforming"),
            ("scale winning", "scale_content",
             0.7, "Scale top-performing content"),
            ("fix mistakes", "run_recovery",
             0.8, "Multiple failures detected, run recovery"),
            ("improve seo", "optimize_seo",
             0.6, "SEO scores below target"),
        ]
        for pattern, decision, confidence, reasoning in rules:
            self.decisions.add_decision_rule(pattern, decision, confidence, reasoning)

    def _init_improvement_handlers(self) -> None:
        def _handle_improvement(params: Dict[str, Any]) -> Dict[str, Any]:
            return {"status": "simulated", "params": params}

        for action_type in ["increase_pin_production", "accelerate_publishing",
                             "rethink_strategy", "scale_content", "run_recovery",
                             "optimize_seo", "implement_fix", "implement_improvement"]:
            self.improvements.register_handler(action_type, _handle_improvement)

    def collect_event(self, module: str, event_type: str, score: float = 0.0,
                      metadata: Optional[Dict[str, Any]] = None,
                      success: bool = True) -> None:
        """Collect a learning event from a module."""
        self.collector.collect(module, event_type, score, metadata, success)

    def record_metric(self, name: str, module: str, value: float,
                      target: float = 0.0, trend: str = "stable") -> None:
        """Record a performance metric."""
        metric = self.analyzer.record_metric(name, module, value, target, trend)
        self.strategy.learn_from_metrics([metric])

    def start_learning_cycle(self) -> Dict[str, Any]:
        """Start continuous learning cycle in background."""
        with self._lock:
            if self._cycle_running:
                return {"status": "already_running"}
            self._cycle_running = True
        self._cycle_thread = threading.Thread(target=self._learning_loop, daemon=True)
        self._cycle_thread.start()
        return {"status": "started"}

    def stop_learning_cycle(self) -> Dict[str, Any]:
        with self._lock:
            self._cycle_running = False
        return {"status": "stopped"}

    def _learning_loop(self) -> None:
        while True:
            with self._lock:
                if not self._cycle_running:
                    break
            try:
                self.run_learning_cycle()
            except Exception:
                pass
            time.sleep(60)  # Run every minute

    def run_learning_cycle(self) -> Dict[str, Any]:
        """Execute one complete learning cycle."""
        with self._lock:
            self._learning_cycles += 1

        # 1. Get all events from collector
        all_events_data = self.collector.get_events(limit=1000)
        # Convert back to LearningEvent-like dicts for analysis
        # (already in dict form from get_events)

        # 2. Analyze performance
        events = []
        for ed in all_events_data:
            evt = self.collector.collect(
                module=ed.get("module", "unknown"),
                event_type=ed.get("event_type", "analyzed"),
                score=ed.get("score", 0.0),
                metadata=ed.get("metadata"),
                success=ed.get("success", True),
            )
            events.append(evt)

        analysis = self.analyzer.analyze_events(events)

        # 3. Detect mistakes
        detected = self.mistakes.detect_from_events(events)

        # 4. Recognize patterns
        patterns = self.patterns.analyze_events(events)

        # 5. Generate recommendations
        recs_from_mistakes = self.recommendations.generate_from_mistakes(detected)
        recs_from_patterns = self.recommendations.generate_from_patterns(patterns)

        # 6. Make decisions
        if analysis.get("success_rate", 100) < 50:
            decision = self.decisions.decide(
                "fix mistakes",
                {"success_rate": analysis["success_rate"], "cycle": self._learning_cycles},
            )
        elif analysis.get("total", 0) > 100 and analysis.get("avg_score", 0) > 0.8:
            decision = self.decisions.decide(
                "scale winning content",
                {"avg_score": analysis["avg_score"]},
            )

        # 7. Apply improvements if recommendations exist
        pending_recs = self.recommendations.get_pending()
        if pending_recs:
            self.improvements.apply_recommendations(pending_recs[:3])

        # 8. Create version snapshot
        if self._learning_cycles % 10 == 0:
            self.versions.create_version(
                changes=f"Learning cycle #{self._learning_cycles}",
                performance_score=analysis.get("avg_score", 0),
            )

        return {
            "cycle": self._learning_cycles,
            "events_analyzed": len(events),
            "mistakes_detected": len(detected),
            "patterns_found": len(patterns),
            "recommendations_generated": len(recs_from_mistakes) + len(recs_from_patterns),
            "improvements_applied": len(pending_recs) if pending_recs else 0,
            "success_rate": analysis.get("success_rate", 100),
            "avg_score": analysis.get("avg_score", 0),
        }

    def get_summary(self) -> LearningSummary:
        summary = LearningSummary()
        c = self.collector.get_stats()
        m = self.mistakes.get_stats()
        r = self.recommendations.get_stats()
        i = self.improvements.get_stats()
        a = self.analyzer.get_stats()

        summary.total_events = c["total_events"]
        summary.total_patterns = self.patterns.get_stats()["total_patterns"]
        summary.total_mistakes = m["total_mistakes"]
        summary.total_recommendations = r["total"]
        summary.improvements_made = i["total_actions"]
        summary.current_version = self.versions.get_current_version()
        summary.avg_performance_score = a.get("total_metrics", 0) / max(
            a.get("metric_types", 1), 1
        )

        return summary

    def get_status(self) -> Dict[str, Any]:
        summary = self.get_summary()
        return {
            "module": "Learning Connector (Layer 23 / Module 13)",
            "version": "1.0.0",
            "learning_cycles": self._learning_cycles,
            "cycle_running": self._cycle_running,
            "uptime_seconds": round(time.time() - self._start_time, 1),
            "collector": self.collector.get_stats(),
            "analyzer": self.analyzer.get_stats(),
            "mistakes": self.mistakes.get_stats(),
            "strategy": self.strategy.get_stats(),
            "prompts": self.prompts.get_stats(),
            "decisions": self.decisions.get_stats(),
            "patterns": self.patterns.get_stats(),
            "knowledge": self.knowledge.get_stats(),
            "recommendations": self.recommendations.get_stats(),
            "improvements": self.improvements.get_stats(),
            "versions": self.versions.get_stats(),
            "memory": self.memory.get_stats(),
            "summary": {
                "total_events": summary.total_events,
                "total_patterns": summary.total_patterns,
                "total_mistakes": summary.total_mistakes,
                "total_recommendations": summary.total_recommendations,
                "improvements_made": summary.improvements_made,
                "current_version": summary.current_version,
            },
        }


# Singleton
_learning_instance: Optional[LearningConnector] = None
_instance_lock = threading.Lock()


def get_learning_connector() -> LearningConnector:
    """Get or create the singleton LearningConnector instance."""
    global _learning_instance
    if _learning_instance is None:
        with _instance_lock:
            if _learning_instance is None:
                _learning_instance = LearningConnector()
    return _learning_instance
