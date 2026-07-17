"""Self-Improvement Manager — Orchestrate the full self-improvement pipeline."""
from __future__ import annotations
import itertools
import time
from typing import Any, Dict, List, Optional

from layers.layer09_learning.modules.self_improvement.improvement_cycle import ImprovementCycle
from layers.layer09_learning.modules.self_improvement.mistake_detector import MistakeDetector
from layers.layer09_learning.modules.self_improvement.weakness_analyzer import WeaknessAnalyzer
from layers.layer09_learning.modules.self_improvement.improvement_actions import ImprovementActionManager
from layers.layer09_learning.modules.self_improvement.experiment_runner import ExperimentRunner
from layers.layer09_learning.modules.self_improvement.improvement_tracker import ImprovementTracker
from layers.layer09_learning.modules.self_improvement.rollback_manager import RollbackManager
from layers.layer09_learning.modules.self_improvement.improvement_metrics import ImprovementMetrics
from layers.layer09_learning.modules.self_improvement.improvement_history import ImprovementHistory

_SMGR_COUNTER = itertools.count(1)


class ImprovementCycleResult:
    """Result of a full self-improvement cycle."""

    __slots__ = (
        "cycle_id", "mistakes_found", "weaknesses_found",
        "actions_created", "actions_completed", "experiments_running",
        "current_score", "improvement_rate", "trend",
        "timestamp", "duration_ms",
    )

    def __init__(self) -> None:
        self.cycle_id: str = f"siy_{next(_SMGR_COUNTER)}"
        self.mistakes_found: int = 0
        self.weaknesses_found: int = 0
        self.actions_created: int = 0
        self.actions_completed: int = 0
        self.experiments_running: int = 0
        self.current_score: float = 0.0
        self.improvement_rate: float = 0.0
        self.trend: str = "insufficient_data"
        self.timestamp: float = time.time()
        self.duration_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cycle_id": self.cycle_id,
            "mistakes_found": self.mistakes_found,
            "weaknesses_found": self.weaknesses_found,
            "actions_created": self.actions_created,
            "current_score": round(self.current_score, 3),
            "improvement_rate": self.improvement_rate,
            "trend": self.trend,
            "duration_ms": round(self.duration_ms, 1),
        }


class SelfImprovementManager:
    """Orchestrate the full self-improvement pipeline.

    Flow: Detect Mistakes → Analyze Weaknesses → Create Actions → Run Experiments → Track
    """

    def __init__(self) -> None:
        self.mistake_detector = MistakeDetector()
        self.weakness_analyzer = WeaknessAnalyzer()
        self.action_manager = ImprovementActionManager()
        self.experiment_runner = ExperimentRunner()
        self.tracker = ImprovementTracker()
        self.rollback_manager = RollbackManager()
        self.metrics = ImprovementMetrics()
        self.history = ImprovementHistory()
        self._cycles: List[ImprovementCycleResult] = []
        self._events: List[Dict[str, Any]] = []

    def run_improvement_cycle(
        self,
        metrics: Optional[Dict[str, float]] = None,
        quality_scores: Optional[Dict[str, float]] = None,
        feedback: Optional[List[Dict[str, Any]]] = None,
        issues: Optional[List[Dict[str, Any]]] = None,
        current_score: float = 0.0,
    ) -> ImprovementCycleResult:
        start = time.time()
        cycle = ImprovementCycle("optimization", "Auto improvement cycle")
        cycle.start()
        result = ImprovementCycleResult()

        # Step 1: Detect mistakes
        mistakes = []
        if metrics and hasattr(self, '_thresholds'):
            mistakes.extend(self.mistake_detector.detect_from_metrics(metrics, self._thresholds))
        if quality_scores:
            mistakes.extend(self.mistake_detector.detect_from_quality(quality_scores))
        if feedback:
            mistakes.extend(self.mistake_detector.detect_from_feedback(feedback))
        result.mistakes_found = len(mistakes)
        self.metrics.record_mistakes(len(mistakes))

        # Step 2: Analyze weaknesses
        weaknesses = []
        if issues:
            weaknesses = self.weakness_analyzer.analyze(issues)
        result.weaknesses_found = len(weaknesses)
        self.metrics.record_weaknesses(len(weaknesses))

        # Step 3: Create actions from mistakes
        actions = self.action_manager.create_from_mistakes(
            [m.to_dict() for m in mistakes]
        )
        result.actions_created = len(actions)

        # Step 4: Complete simple actions
        completed = 0
        for action in actions:
            if action.priority in ("low", "medium"):
                action.complete(0.5)
                self.action_manager.complete_action(action.action_id, 0.5)
                completed += 1
                self.metrics.record_action(completed=True)
        result.actions_completed = completed

        # Step 5: Track snapshot
        self.tracker.take_snapshot(
            current_score,
            weaknesses_resolved=len(weaknesses),
            actions_completed=completed,
        )

        # Step 6: Record history
        trend = self.tracker.get_trend()
        improvement_rate = self.tracker.get_improvement_rate()
        result.trend = trend
        result.improvement_rate = improvement_rate
        result.current_score = current_score

        if mistakes:
            self.history.record(
                "mistake_fix", f"Detected {len(mistakes)} mistakes",
                score_before=current_score, score_after=current_score,
            )

        # Step 7: Record metrics
        successful = result.actions_completed > 0
        self.metrics.record_cycle(current_score, successful)

        cycle.complete(result.actions_created)
        result.duration_ms = (time.time() - start) * 1000
        self._cycles.append(result)
        self._events.append({
            "event": "improvement_cycle_completed",
            "cycle_id": result.cycle_id,
            "mistakes": result.mistakes_found,
            "actions": result.actions_created,
        })
        return result

    def create_experiment(self, hypothesis: str, control_metric: str = "",
                          control_value: float = 0.0):
        return self.experiment_runner.create_experiment(hypothesis, control_metric, control_value)

    def save_checkpoint(self, label: str, state: Dict[str, Any]) -> Dict[str, Any]:
        point = self.rollback_manager.save_point(label, state)
        return point.to_dict()

    def rollback_to(self, point_id: str) -> Optional[Dict[str, Any]]:
        result = self.rollback_manager.rollback(point_id)
        if result:
            self.metrics.record_rollback()
        return result

    def get_health(self) -> Dict[str, Any]:
        return {
            "total_cycles": len(self._cycles),
            "tracker_trend": self.tracker.get_trend(),
            "best_score": self.tracker.get_best_score(),
            "rollback_points": self.rollback_manager.point_count,
            "metrics": self.metrics.get_summary(),
        }

    def get_recent_cycles(self, count: int = 5) -> List[ImprovementCycleResult]:
        return list(self._cycles[-count:])

    @property
    def events(self) -> List[Dict[str, Any]]:
        return list(self._events)

    @property
    def cycle_count(self) -> int:
        return len(self._cycles)
