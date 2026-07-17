"""Optimization Manager — Orchestrate the full content optimization pipeline."""
from __future__ import annotations
import itertools
import time
from typing import Any, Dict, List, Optional

from layers.layer09_learning.modules.content_optimization.optimization_profile import OptimizationProfile
from layers.layer09_learning.modules.content_optimization.content_analyzer import ContentAnalyzer
from layers.layer09_learning.modules.content_optimization.optimization_rules import RuleLibrary
from layers.layer09_learning.modules.content_optimization.suggestion_generator import SuggestionGenerator
from layers.layer09_learning.modules.content_optimization.rewrite_engine import RewriteEngine
from layers.layer09_learning.modules.content_optimization.variant_evaluator import VariantEvaluator
from layers.layer09_learning.modules.content_optimization.optimization_memory import OptimizationMemory
from layers.layer09_learning.modules.content_optimization.optimization_metrics import OptimizationMetrics
from layers.layer09_learning.modules.content_optimization.optimization_validator import OptimizationValidator

_OMGR_COUNTER = itertools.count(1)


class OptimizationResult:
    """Result of a full content optimization cycle."""

    __slots__ = (
        "result_id", "original", "optimized", "analysis",
        "suggestions_applied", "variant_score", "improvement_pct",
        "validation_passed", "memory_stored", "timestamp", "duration_ms",
    )

    def __init__(self, original: str = "") -> None:
        self.result_id: str = f"ocr_{next(_OMGR_COUNTER)}"
        self.original = original
        self.optimized: str = ""
        self.analysis = None
        self.suggestions_applied: int = 0
        self.variant_score: float = 0.0
        self.improvement_pct: float = 0.0
        self.validation_passed: bool = True
        self.memory_stored: bool = False
        self.timestamp: float = time.time()
        self.duration_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "result_id": self.result_id,
            "suggestions_applied": self.suggestions_applied,
            "variant_score": round(self.variant_score, 3),
            "improvement_pct": round(self.improvement_pct, 2),
            "validation_passed": self.validation_passed,
            "memory_stored": self.memory_stored,
            "duration_ms": round(self.duration_ms, 1),
        }


class OptimizationManager:
    """Orchestrate the full content optimization pipeline.

    Flow: Analyze → Generate Suggestions → Rewrite → Evaluate → Validate → Store
    """

    def __init__(self) -> None:
        self.analyzer = ContentAnalyzer()
        self.rules = RuleLibrary()
        self.suggestion_generator = SuggestionGenerator()
        self.rewrite_engine = RewriteEngine()
        self.evaluator = VariantEvaluator()
        self.memory = OptimizationMemory()
        self.metrics = OptimizationMetrics()
        self.validator = OptimizationValidator()
        self._results: List[OptimizationResult] = []
        self._events: List[Dict[str, Any]] = []

    def optimize(self, content: str, profile: Optional[OptimizationProfile] = None,
                 brand_terms: Optional[List[str]] = None,
                 forbidden_terms: Optional[List[str]] = None) -> OptimizationResult:
        start = time.time()
        result = OptimizationResult(content)
        profile = profile or OptimizationProfile()

        # Step 1: Analyze content
        analysis = self.analyzer.analyze(content, platform=profile.platform)
        result.analysis = analysis.to_dict()

        # Step 2: Generate suggestions
        suggestions = self.suggestion_generator.generate(
            content, result.analysis,
            goal=profile.goal,
            max_suggestions=profile.max_suggestions,
        )
        self.metrics.record_suggestions(len(suggestions))

        # Step 3: Rewrite
        suggestion_dicts = [s.to_dict() for s in suggestions]
        variant = self.rewrite_engine.rewrite(content, suggestion_dicts, profile.preserve_meaning)
        result.optimized = variant.content
        result.suggestions_applied = variant.changes_made
        self.metrics.record_variant()

        # Step 4: Evaluate
        comparison = self.evaluator.evaluate(content, variant.content, variant.variant_id)
        result.variant_score = comparison.variant_score
        result.improvement_pct = comparison.improvement_pct

        # Step 5: Validate
        validation = self.validator.validate(variant.content, brand_terms=brand_terms,
                                             forbidden_terms=forbidden_terms)
        result.validation_passed = validation.is_valid

        # Step 6: Store in memory
        if result.validation_passed and result.improvement_pct > 0:
            self.memory.store(
                pattern_type=profile.goal,
                description=f"Optimized content improved by {result.improvement_pct:.1f}%",
                context={"platform": profile.platform, "content_type": profile.content_type},
                success_rate=min(1.0, 0.5 + result.improvement_pct / 100),
                tags=[profile.goal, profile.platform],
            )
            result.memory_stored = True

        # Step 7: Record metrics
        self.metrics.record_optimization(result.improvement_pct, result.validation_passed)

        result.duration_ms = (time.time() - start) * 1000
        self._results.append(result)
        self._events.append({
            "event": "optimization_completed",
            "result_id": result.result_id,
            "improvement_pct": result.improvement_pct,
            "valid": result.validation_passed,
        })
        return result

    def get_health(self) -> Dict[str, Any]:
        return {
            "total_optimizations": len(self._results),
            "rule_count": self.rules.rule_count,
            "memory_stats": self.memory.get_stats(),
            "metrics": self.metrics.get_summary(),
        }

    def get_recent_results(self, count: int = 5) -> List[OptimizationResult]:
        return list(self._results[-count:])

    @property
    def events(self) -> List[Dict[str, Any]]:
        return list(self._events)

    @property
    def optimization_count(self) -> int:
        return len(self._results)
