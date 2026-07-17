"""Learning Manager — Orchestrate the full learning pipeline."""
from __future__ import annotations
import itertools
import time
from typing import Any, Dict, List, Optional

from layers.layer09_learning.modules.learning_engine.learning_signal import LearningSignal
from layers.layer09_learning.modules.learning_engine.feedback_collector import FeedbackCollector
from layers.layer09_learning.modules.learning_engine.performance_comparator import PerformanceComparator
from layers.layer09_learning.modules.learning_engine.pattern_detector import PatternDetector, DetectedPattern
from layers.layer09_learning.modules.learning_engine.lesson_generator import LessonGenerator
from layers.layer09_learning.modules.learning_engine.improvement_planner import ImprovementPlanner, Improvement
from layers.layer09_learning.modules.learning_engine.learning_memory import LearningMemory
from layers.layer09_learning.modules.learning_engine.confidence_tracker import ConfidenceTracker
from layers.layer09_learning.modules.learning_engine.learning_metrics import LearningMetrics

_MANAGER_COUNTER = itertools.count(1)


class LearningResult:
    """Result of a complete learning cycle."""

    __slots__ = (
        "result_id", "lessons", "mistakes", "improvements",
        "confidence", "learning_score", "success_patterns",
        "failure_patterns", "next_actions", "version", "timestamp",
    )

    def __init__(self) -> None:
        self.result_id: str = f"lrn_{next(_MANAGER_COUNTER)}"
        self.lessons: List[Dict[str, Any]] = []
        self.mistakes: List[Dict[str, Any]] = []
        self.improvements: List[Dict[str, Any]] = []
        self.confidence: float = 0.0
        self.learning_score: float = 0.0
        self.success_patterns: int = 0
        self.failure_patterns: int = 0
        self.next_actions: List[str] = []
        self.version: int = 1
        self.timestamp: float = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "result_id": self.result_id,
            "lesson_count": len(self.lessons),
            "mistake_count": len(self.mistakes),
            "improvement_count": len(self.improvements),
            "confidence": round(self.confidence, 3),
            "learning_score": round(self.learning_score, 2),
            "success_patterns": self.success_patterns,
            "failure_patterns": self.failure_patterns,
            "next_action_count": len(self.next_actions),
            "version": self.version,
        }


class LearningManager:
    """Orchestrate the full learning pipeline.

    Flow: Collect → Compare → Detect Patterns → Generate Lessons → Plan Improvements → Store
    """

    def __init__(self) -> None:
        self.feedback_collector = FeedbackCollector()
        self.comparator = PerformanceComparator()
        self.pattern_detector = PatternDetector()
        self.lesson_generator = LessonGenerator()
        self.improvement_planner = ImprovementPlanner()
        self.learning_memory = LearningMemory()
        self.confidence_tracker = ConfidenceTracker()
        self.metrics = LearningMetrics()
        self._results: List[LearningResult] = []
        self._events: List[Dict[str, Any]] = []

    def run_learning_cycle(
        self,
        signals: List[LearningSignal],
        previous_signals: Optional[List[LearningSignal]] = None,
    ) -> LearningResult:
        result = LearningResult()

        # Step 1: Detect patterns
        patterns = self.pattern_detector.detect(signals)
        success_patterns = [p for p in patterns if p.pattern_type == "success"]
        failure_patterns = [p for p in patterns if p.pattern_type == "failure"]
        result.success_patterns = len(success_patterns)
        result.failure_patterns = len(failure_patterns)

        # Step 2: Compare performance
        if previous_signals:
            comparisons = self.comparator.compare_signals(previous_signals, signals)
            for comp in comparisons:
                self.confidence_tracker.record(
                    comp.metric_name,
                    confidence=0.8 if comp.direction == "growth" else 0.6,
                )

        # Step 3: Generate lessons
        lessons = self.lesson_generator.generate(patterns)
        for lesson in lessons:
            entry = self.learning_memory.store_lesson(lesson)
            if lesson.lesson_type == "best_practice":
                result.lessons.append(lesson.to_dict())
            elif lesson.lesson_type == "mistake":
                result.mistakes.append(lesson.to_dict())

        # Step 4: Plan improvements
        improvements = self.improvement_planner.plan_from_lessons(lessons)
        for imp in improvements:
            self.learning_memory.store_improvement(imp)
            result.improvements.append(imp.to_dict())

        # Step 5: Compute metrics
        self.metrics.record_learning_cycle(
            signals=len(signals),
            patterns=len(patterns),
            lessons=len(lessons),
            improvements=len(improvements),
        )
        result.learning_score = self.metrics.get_score()
        result.confidence = self.confidence_tracker.get_overall_reliability()

        # Step 6: Generate next actions
        result.next_actions = self._generate_next_actions(
            success_patterns, failure_patterns, improvements
        )

        # Store result
        self._results.append(result)
        self._events.append({
            "event": "learning_cycle_completed",
            "result_id": result.result_id,
            "score": result.learning_score,
        })
        return result

    def get_recent_results(self, count: int = 5) -> List[LearningResult]:
        return list(self._results[-count:])

    def get_health(self) -> Dict[str, Any]:
        return {
            "total_cycles": len(self._results),
            "memory_stats": self.learning_memory.get_stats(),
            "confidence_reliability": self.confidence_tracker.get_overall_reliability(),
            "learning_metrics": self.metrics.get_summary(),
        }

    def _generate_next_actions(
        self,
        success_patterns: List[DetectedPattern],
        failure_patterns: List[DetectedPattern],
        improvements: List[Improvement],
    ) -> List[str]:
        actions = []
        if failure_patterns:
            actions.append(f"Investigate {len(failure_patterns)} failure patterns")
        if success_patterns:
            actions.append(f"Replicate {len(success_patterns)} success patterns")
        critical = [i for i in improvements if i.priority == "critical"]
        if critical:
            actions.append(f"Address {len(critical)} critical improvements")
        if not actions:
            actions.append("Continue monitoring for new patterns")
        return actions

    @property
    def events(self) -> List[Dict[str, Any]]:
        return list(self._events)

    @property
    def cycle_count(self) -> int:
        return len(self._results)
