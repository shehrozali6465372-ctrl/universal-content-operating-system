"""Experiment Runner — Run and track improvement experiments."""
from __future__ import annotations
import time
import itertools
from typing import Any, Dict, List, Optional

_ER_COUNTER = itertools.count(1)

EXPERIMENT_STATUSES = ("hypothesis", "running", "concluded", "failed", "cancelled")


class Experiment:
    """A controlled experiment to test improvement hypotheses."""

    __slots__ = ("experiment_id", "status", "hypothesis", "description",
                 "control_metric", "control_value", "treatment_metric", "treatment_value",
                 "start_time", "end_time", "duration_ms",
                 "sample_size", "confidence", "conclusion", "metadata")

    def __init__(self, hypothesis: str = "") -> None:
        self.experiment_id: str = f"exp_{next(_ER_COUNTER)}"
        self.status: str = "hypothesis"
        self.hypothesis = hypothesis
        self.description: str = ""
        self.control_metric: str = ""
        self.control_value: float = 0.0
        self.treatment_metric: str = ""
        self.treatment_value: float = 0.0
        self.start_time: float = 0.0
        self.end_time: float = 0.0
        self.duration_ms: float = 0.0
        self.sample_size: int = 0
        self.confidence: float = 0.0
        self.conclusion: str = ""
        self.metadata: Dict[str, Any] = {}

    def start(self) -> None:
        self.status = "running"
        self.start_time = time.time()

    def conclude(self, winner: str = "", confidence: float = 0.0) -> None:
        self.status = "concluded"
        self.end_time = time.time()
        self.duration_ms = round((self.end_time - self.start_time) * 1000, 1)
        self.confidence = confidence
        self.conclusion = winner

    @property
    def improvement_pct(self) -> float:
        if self.control_value == 0:
            return 0.0
        return round(((self.treatment_value - self.control_value) / abs(self.control_value)) * 100, 2)

    @property
    def is_significant(self) -> bool:
        return self.confidence >= 0.95 and self.sample_size >= 30

    def to_dict(self) -> Dict[str, Any]:
        return {
            "experiment_id": self.experiment_id,
            "status": self.status,
            "hypothesis": self.hypothesis,
            "improvement_pct": self.improvement_pct,
            "confidence": round(self.confidence, 3),
            "conclusion": self.conclusion,
            "is_significant": self.is_significant,
        }


class ExperimentRunner:
    """Create, run, and evaluate improvement experiments."""

    def __init__(self) -> None:
        self._experiments: List[Experiment] = []

    def create_experiment(self, hypothesis: str, control_metric: str = "",
                          control_value: float = 0.0) -> Experiment:
        exp = Experiment(hypothesis)
        exp.control_metric = control_metric
        exp.control_value = control_value
        self._experiments.append(exp)
        return exp

    def record_treatment(self, experiment_id: str, treatment_metric: str,
                         treatment_value: float, sample_size: int = 10) -> Optional[Experiment]:
        exp = self.get_experiment(experiment_id)
        if not exp:
            return None
        exp.treatment_metric = treatment_metric
        exp.treatment_value = treatment_value
        exp.sample_size = sample_size
        return exp

    def evaluate(self, experiment_id: str, confidence: float = 0.0) -> Optional[Experiment]:
        exp = self.get_experiment(experiment_id)
        if not exp:
            return None
        if exp.treatment_value > exp.control_value:
            exp.conclude("treatment", confidence)
        elif exp.treatment_value < exp.control_value:
            exp.conclude("control", confidence)
        else:
            exp.conclude("no_difference", confidence)
        return exp

    def get_experiment(self, experiment_id: str) -> Optional[Experiment]:
        for e in self._experiments:
            if e.experiment_id == experiment_id:
                return e
        return None

    def get_experiments(self, status: str = "") -> List[Experiment]:
        if status:
            return [e for e in self._experiments if e.status == status]
        return list(self._experiments)

    def get_significant(self) -> List[Experiment]:
        return [e for e in self._experiments if e.is_significant]

    @property
    def experiment_count(self) -> int:
        return len(self._experiments)
