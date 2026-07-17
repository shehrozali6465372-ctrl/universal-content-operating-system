"""Prompt Manager — Orchestrate the full prompt optimization pipeline."""
from __future__ import annotations
import itertools
import time
from typing import Any, Dict, List, Optional

from layers.layer09_learning.modules.prompt_optimization.prompt_profile import PromptProfile
from layers.layer09_learning.modules.prompt_optimization.prompt_history import PromptHistory
from layers.layer09_learning.modules.prompt_optimization.prompt_comparator import PromptComparator
from layers.layer09_learning.modules.prompt_optimization.prompt_analyzer import PromptAnalyzer, AnalysisReport
from layers.layer09_learning.modules.prompt_optimization.prompt_optimizer import (
    PromptOptimizer, OptimizationResult,
)
from layers.layer09_learning.modules.prompt_optimization.prompt_variants import PromptVariants
from layers.layer09_learning.modules.prompt_optimization.prompt_memory import PromptMemory
from layers.layer09_learning.modules.prompt_optimization.prompt_metrics import PromptMetrics
from layers.layer09_learning.modules.prompt_optimization.prompt_validator import PromptValidator

_MANAGER_COUNTER = itertools.count(1)


class OptimizationCycleResult:
    """Result of a full prompt optimization cycle."""

    __slots__ = (
        "cycle_id", "profile_id", "analysis", "optimization",
        "validation_score", "is_approved", "improvements_suggested",
        "timestamp", "duration_ms",
    )

    def __init__(self, profile_id: str = "") -> None:
        self.cycle_id: str = f"poc_{next(_MANAGER_COUNTER)}"
        self.profile_id = profile_id
        self.analysis: Optional[AnalysisReport] = None
        self.optimization: Optional[OptimizationResult] = None
        self.validation_score: float = 0.0
        self.is_approved: bool = False
        self.improvements_suggested: int = 0
        self.timestamp: float = time.time()
        self.duration_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cycle_id": self.cycle_id,
            "profile_id": self.profile_id,
            "analysis_health": self.analysis.overall_health if self.analysis else "unknown",
            "improvements_suggested": self.improvements_suggested,
            "validation_score": round(self.validation_score, 2),
            "is_approved": self.is_approved,
            "duration_ms": round(self.duration_ms, 1),
        }


class PromptManager:
    """Orchestrate the full prompt optimization pipeline.

    Flow: Analyze → Optimize → Validate → Store Learnings
    """

    def __init__(self) -> None:
        self.history = PromptHistory()
        self.comparator = PromptComparator()
        self.analyzer = PromptAnalyzer()
        self.optimizer = PromptOptimizer()
        self.variants = PromptVariants()
        self.memory = PromptMemory()
        self.metrics = PromptMetrics()
        self.validator = PromptValidator()
        self._cycles: List[OptimizationCycleResult] = []
        self._events: List[Dict[str, Any]] = []

    def run_optimization_cycle(self, profile: PromptProfile) -> OptimizationCycleResult:
        start = time.time()
        result = OptimizationCycleResult(profile.profile_id)

        # Step 1: Analyze
        analysis = self.analyzer.analyze(profile)
        result.analysis = analysis
        self.metrics.record_analysis()

        # Step 2: Optimize
        optimization = self.optimizer.optimize(profile, analysis)
        result.optimization = optimization
        result.improvements_suggested = optimization.changes_made
        improved = optimization.changes_made > 0
        self.metrics.record_optimization(optimization.confidence, improved)

        # Step 3: Validate
        validation = self.validator.validate(profile)
        result.validation_score = validation.score
        result.is_approved = validation.is_valid

        # Step 4: Store learnings
        if analysis.findings:
            self.memory.store(
                profile.profile_id, "analysis",
                f"Analysis found {len(analysis.findings)} findings",
                confidence=analysis.score / 100.0,
                tags=[profile.category, profile.platform],
            )

        # Step 5: Record history
        self.history.record(
            profile, "optimized",
            {"engagement": profile.avg_engagement, "quality": profile.avg_quality_score},
            notes=f"Optimization cycle: {optimization.changes_made} suggestions",
        )

        result.duration_ms = (time.time() - start) * 1000
        self._cycles.append(result)
        self._events.append({
            "event": "optimization_cycle_completed",
            "cycle_id": result.cycle_id,
            "profile_id": profile.profile_id,
            "approved": result.is_approved,
        })
        return result

    def compare_prompts(self, baseline: PromptProfile, candidate: PromptProfile) -> str:
        winner = self.comparator.get_overall_winner(baseline, candidate)
        results = self.comparator.get_results()
        if results:
            self.metrics.record_comparison(
                sum(r.change_pct for r in results) / len(results)
            )
        return winner

    def create_ab_test(self, name: str, baseline: PromptProfile,
                       candidates: List[PromptProfile], min_samples: int = 10):
        test = self.variants.create_test(name, baseline, candidates, min_samples)
        self.metrics.record_variant_test()
        return test

    def get_health(self) -> Dict[str, Any]:
        return {
            "total_cycles": len(self._cycles),
            "history_entries": self.history.entry_count,
            "memory_stats": self.memory.get_stats(),
            "metrics": self.metrics.get_summary(),
            "validation_invalid": self.validator.get_invalid_count(),
        }

    def get_recent_cycles(self, count: int = 5) -> List[OptimizationCycleResult]:
        return list(self._cycles[-count:])

    @property
    def events(self) -> List[Dict[str, Any]]:
        return list(self._events)

    @property
    def cycle_count(self) -> int:
        return len(self._cycles)
