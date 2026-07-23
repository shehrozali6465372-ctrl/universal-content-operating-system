"""SelfImprovementManager — Master integrator for all 7 self-improvement modules."""
from __future__ import annotations
import threading
import time
from typing import Any, Dict, List, Optional

from .performance_analyzer import PerformanceAnalyzer, get_performance_analyzer
from .mistake_detection_engine import MistakeDetectionEngine, get_mistake_detection
from .strategy_optimizer import StrategyOptimizer, get_strategy_optimizer
from .prompt_optimizer import PromptOptimizer, get_prompt_optimizer
from .ab_testing_engine import ABTestingEngine, get_ab_testing_engine
from .knowledge_evolution_engine import KnowledgeEvolutionEngine, get_knowledge_evolution


class SelfImprovementManager:
    """Master integrator for Self-Improvement & Business Strategy Engine."""
    _instance: Optional["SelfImprovementManager"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "SelfImprovementManager":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True
        self._performance = get_performance_analyzer()
        self._mistakes = get_mistake_detection()
        self._strategy = get_strategy_optimizer()
        self._prompts = get_prompt_optimizer()
        self._ab_testing = get_ab_testing_engine()
        self._knowledge = get_knowledge_evolution()
        self._initialized_at = time.time()

    @property
    def performance(self) -> PerformanceAnalyzer:
        return self._performance

    @property
    def mistakes(self) -> MistakeDetectionEngine:
        return self._mistakes

    @property
    def strategy(self) -> StrategyOptimizer:
        return self._strategy

    @property
    def prompts(self) -> PromptOptimizer:
        return self._prompts

    @property
    def ab_testing(self) -> ABTestingEngine:
        return self._ab_testing

    @property
    def knowledge(self) -> KnowledgeEvolutionEngine:
        return self._knowledge

    def analyze_and_improve(self) -> Dict[str, Any]:
        perf_report = self._performance.get_analysis_report()
        active_mistakes = self._mistakes.get_active_patterns()
        pending_recs = self._strategy.get_pending()
        return {
            "performance_summary": {
                "total_records": perf_report["total_records"],
                "avg_score": perf_report["avg_performance_score"],
                "total_revenue": perf_report["total_revenue"],
            },
            "active_mistakes": len(active_mistakes),
            "critical_mistakes": sum(1 for m in active_mistakes if m.severity == "critical"),
            "pending_recommendations": len(pending_recs),
            "running_experiments": len(self._ab_testing.get_running()),
            "knowledge_entries": self._knowledge.stats()["entries"],
            "improvement_actions": self._generate_improvement_actions(),
        }

    def _generate_improvement_actions(self) -> List[str]:
        actions = []
        critical = self._mistakes.get_active_patterns("critical")
        if critical:
            actions.append(f"🚨 {len(critical)} critical mistakes need immediate attention")
        pending = self._strategy.get_pending()
        if pending:
            actions.append(f"📋 {len(pending)} strategy recommendations pending")
        worst_prompts = self._prompts.get_worst_prompts(min_uses=3, limit=3)
        if worst_prompts:
            actions.append(f"🔄 {len(worst_prompts)} prompts need improvement")
        running = self._ab_testing.get_running()
        if running:
            actions.append(f"🧪 {len(running)} A/B tests running")
        stale = self._knowledge.get_stale_entries(30)
        if stale:
            actions.append(f"📚 {len(stale)} knowledge entries need validation")
        if not actions:
            actions.append("✅ System performing well — no immediate actions needed")
        return actions

    def get_full_status(self) -> Dict[str, Any]:
        return {
            "overall": "Active",
            "uptime_seconds": round(time.time() - self._initialized_at, 2),
            "performance": self._performance.get_analysis_report(),
            "mistakes": self._mistakes.get_detection_report(),
            "strategy": self._strategy.get_strategy_status(),
            "prompts": self._prompts.get_optimization_report(),
            "ab_testing": self._ab_testing.get_testing_status(),
            "knowledge": self._knowledge.get_knowledge_report(),
        }

    def get_executive_summary(self) -> Dict[str, Any]:
        perf = self._performance.get_analysis_report()
        mistakes = self._mistakes.get_detection_report()
        strategy = self._strategy.get_strategy_status()
        prompts = self._prompts.get_optimization_report()
        ab = self._ab_testing.get_testing_status()
        knowledge = self._knowledge.get_knowledge_report()
        return {
            "total_performance_records": perf["total_records"],
            "total_revenue": perf["total_revenue"],
            "active_mistakes": mistakes["active"],
            "strategy_recommendations": strategy["pending"],
            "active_prompts": prompts["active"],
            "running_experiments": ab["running"],
            "knowledge_entries": knowledge["active"],
            "improvement_actions": self._generate_improvement_actions(),
        }

    def stats(self) -> Dict[str, Any]:
        return {
            "performance": self._performance.stats(),
            "mistakes": self._mistakes.stats(),
            "strategy": self._strategy.stats(),
            "prompts": self._prompts.stats(),
            "ab_testing": self._ab_testing.stats(),
            "knowledge": self._knowledge.stats(),
        }


def get_self_improvement() -> SelfImprovementManager:
    return SelfImprovementManager()
