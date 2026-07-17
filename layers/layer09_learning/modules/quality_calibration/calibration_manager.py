"""Calibration Manager — Orchestrate the full calibration pipeline."""
from __future__ import annotations
import itertools
import time
from typing import Any, Dict, List, Optional

from layers.layer09_learning.modules.quality_calibration.calibration_profile import CalibrationProfile
from layers.layer09_learning.modules.quality_calibration.threshold_manager import ThresholdManager
from layers.layer09_learning.modules.quality_calibration.score_adjuster import ScoreAdjuster
from layers.layer09_learning.modules.quality_calibration.confidence_calibrator import ConfidenceCalibrator
from layers.layer09_learning.modules.quality_calibration.evaluator import Evaluator
from layers.layer09_learning.modules.quality_calibration.benchmark_manager import BenchmarkManager
from layers.layer09_learning.modules.quality_calibration.calibration_history import CalibrationHistory
from layers.layer09_learning.modules.quality_calibration.calibration_metrics import CalibrationMetrics
from layers.layer09_learning.modules.quality_calibration.calibration_validator import CalibrationValidator

_CMGR_COUNTER = itertools.count(1)


class CalibrationCycleResult:
    """Result of a full calibration cycle."""

    __slots__ = ("cycle_id", "metrics_calibrated", "bias_updates",
                 "ece", "mae", "validation_score", "is_valid",
                 "timestamp", "duration_ms")

    def __init__(self) -> None:
        self.cycle_id: str = f"ccy_{next(_CMGR_COUNTER)}"
        self.metrics_calibrated: int = 0
        self.bias_updates: int = 0
        self.ece: float = 0.0
        self.mae: float = 0.0
        self.validation_score: float = 100.0
        self.is_valid: bool = True
        self.timestamp: float = time.time()
        self.duration_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cycle_id": self.cycle_id,
            "metrics_calibrated": self.metrics_calibrated,
            "bias_updates": self.bias_updates,
            "ece": round(self.ece, 4),
            "mae": round(self.mae, 4),
            "validation_score": round(self.validation_score, 2),
            "is_valid": self.is_valid,
            "duration_ms": round(self.duration_ms, 1),
        }


class CalibrationManager:
    """Orchestrate the full quality calibration pipeline.

    Flow: Evaluate → Calibrate Confidence → Adjust Scores → Validate → Benchmark
    """

    def __init__(self) -> None:
        self.profiles: Dict[str, CalibrationProfile] = {}
        self.thresholds = ThresholdManager()
        self.adjuster = ScoreAdjuster()
        self.confidence_calibrator = ConfidenceCalibrator()
        self.evaluator = Evaluator()
        self.benchmark_manager = BenchmarkManager()
        self.history = CalibrationHistory()
        self.metrics = CalibrationMetrics()
        self.validator = CalibrationValidator()
        self._cycles: List[CalibrationCycleResult] = []
        self._events: List[Dict[str, Any]] = []

    def run_calibration_cycle(
        self,
        predicted_scores: Dict[str, float],
        actual_scores: Dict[str, float],
        confidence_predictions: Optional[List[Dict[str, float]]] = None,
    ) -> CalibrationCycleResult:
        start = time.time()
        result = CalibrationCycleResult()

        # Step 1: Evaluate predictions
        evaluations = self.evaluator.evaluate(predicted_scores, actual_scores)
        mae = self.evaluator.get_mae()
        result.mae = mae
        self.metrics.record_evaluation(mae)

        # Step 2: Update profiles and biases
        for eval_result in evaluations:
            metric = eval_result.metric
            if metric not in self.profiles:
                self.profiles[metric] = CalibrationProfile(metric)
            profile = self.profiles[metric]
            old_bias = profile.bias
            profile.update(eval_result.predicted, eval_result.actual)
            if abs(profile.bias) > 0.01:
                self.adjuster.set_bias(metric, -profile.bias, profile.calibration_accuracy)
                self.history.record(
                    metric, old_bias, profile.bias,
                    trigger="calibration_cycle",
                )
                result.bias_updates += 1
            result.metrics_calibrated += 1

        # Step 3: Confidence calibration
        ece = 0.0
        if confidence_predictions:
            self.confidence_calibrator.calibrate(confidence_predictions)
            ece = self.confidence_calibrator.get_overall_ece()
        result.ece = ece
        self.metrics.record_calibration(ece)

        # Step 4: Validate
        biases = {m: p.bias for m, p in self.profiles.items()}
        sample_counts = {m: p.calibration_count for m, p in self.profiles.items()}
        validation = self.validator.validate(biases, sample_counts, ece)
        result.validation_score = validation.score
        result.is_valid = validation.is_valid

        # Step 5: Record benchmark
        benchmark_scores = {m: p.actual_weight for m, p in self.profiles.items()}
        if benchmark_scores:
            self.benchmark_manager.create_run("calibration", benchmark_scores)
            self.metrics.record_benchmark()

        result.duration_ms = (time.time() - start) * 1000
        self._cycles.append(result)
        self._events.append({
            "event": "calibration_cycle_completed",
            "cycle_id": result.cycle_id,
            "valid": result.is_valid,
        })
        return result

    def adjust_scores(self, scores: Dict[str, float]) -> Dict[str, float]:
        results = self.adjuster.adjust_batch(scores)
        self.metrics.record_adjustment()
        return {r.metric: r.adjusted_score for r in results}

    def evaluate_threshold(self, metric: str, value: float,
                           context: str = "default") -> Dict[str, Any]:
        return self.thresholds.evaluate(metric, value, context)

    def get_health(self) -> Dict[str, Any]:
        return {
            "total_cycles": len(self._cycles),
            "profiles": len(self.profiles),
            "benchmark_runs": self.benchmark_manager.run_count,
            "history_entries": self.history.entry_count,
            "metrics": self.metrics.get_summary(),
        }

    def get_recent_cycles(self, count: int = 5) -> List[CalibrationCycleResult]:
        return list(self._cycles[-count:])

    @property
    def events(self) -> List[Dict[str, Any]]:
        return list(self._events)

    @property
    def cycle_count(self) -> int:
        return len(self._cycles)
