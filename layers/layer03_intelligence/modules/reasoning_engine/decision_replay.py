"""Decision Replay - Records and replays decision sequences."""
from __future__ import annotations
import copy
import math
import time
from threading import RLock
from typing import Any, Dict, List, Optional


class ReplayStep:
    """A single step in a decision replay."""
    __slots__ = ("step_id", "stage", "input_data", "output_data",
                 "decision", "confidence", "timestamp", "duration_ms")

    def __init__(self, step_id: int = 0, stage: str = ""):
        self.step_id = step_id
        self.stage = stage
        self.input_data: Dict[str, Any] = {}
        self.output_data: Dict[str, Any] = {}
        self.decision = ""
        self.confidence = 0.0
        self.timestamp = time.time()
        self.duration_ms = 0.0

    def to_dict(self) -> Dict:
        return {
            "step": self.step_id, "stage": self.stage,
            "decision": self.decision, "confidence": round(self.confidence, 3),
            "duration_ms": round(self.duration_ms, 1),
            "input_keys": list(self.input_data.keys()),
            "output_keys": list(self.output_data.keys()),
        }


class DecisionReplay:
    """Records and replays a complete decision sequence."""

    def __init__(self, topic: str = "", replay_id: str = "", max_steps: int = 100) -> None:
        if max_steps < 1:
            raise ValueError("max_steps must be >= 1")
        self.topic = topic
        self.replay_id = replay_id
        self.steps: List[ReplayStep] = []
        self.max_steps = max_steps
        self.final_decision = ""
        self.final_confidence = 0.0
        self.outcome = "pending"
        self.created_at = time.time()

    def add_step(self, stage: str, decision: str = "", confidence: float = 0.0,
                 input_data: Optional[Dict] = None, output_data: Optional[Dict] = None,
                 duration_ms: float = 0.0) -> ReplayStep:
        if len(self.steps) >= self.max_steps:
            raise ValueError("replay step limit exceeded")
        if not math.isfinite(confidence) or not 0.0 <= confidence <= 1.0:
            raise ValueError("confidence must be finite and between 0 and 1")
        if not math.isfinite(duration_ms) or duration_ms < 0:
            raise ValueError("duration_ms must be finite and non-negative")
        step = ReplayStep(len(self.steps) + 1, stage)
        step.decision = decision
        step.confidence = confidence
        step.input_data = copy.deepcopy(input_data or {})
        step.output_data = copy.deepcopy(output_data or {})
        step.duration_ms = duration_ms
        self.steps.append(step)
        return step

    def finalize(self, decision: str, confidence: float) -> None:
        if not math.isfinite(confidence) or not 0.0 <= confidence <= 1.0:
            raise ValueError("confidence must be finite and between 0 and 1")
        self.final_decision = decision
        self.final_confidence = confidence

    def get_stage_decisions(self) -> List[Dict]:
        return [{"stage": s.stage, "decision": s.decision, "confidence": s.confidence}
                for s in self.steps]

    def get_path(self) -> str:
        return " -> ".join(s.stage for s in self.steps) if self.steps else "empty"

    def to_dict(self) -> Dict:
        return {
            "topic": self.topic, "replay_id": self.replay_id,
            "steps": [s.to_dict() for s in self.steps],
            "final_decision": self.final_decision,
            "final_confidence": round(self.final_confidence, 3),
            "outcome": self.outcome, "path": self.get_path(),
            "step_count": len(self.steps),
        }


class ReplayStore:
    """Stores decision replays for analysis and learning."""

    def __init__(self, max_replays: int = 500) -> None:
        if max_replays < 1:
            raise ValueError("max_replays must be >= 1")
        self._replays: List[DecisionReplay] = []
        self._max = max_replays
        self._lock = RLock()

    def record(self, replay: DecisionReplay) -> None:
        with self._lock:
            self._replays.append(copy.deepcopy(replay))
            if len(self._replays) > self._max:
                self._replays = self._replays[-self._max:]

    def get_by_topic(self, topic: str) -> List[DecisionReplay]:
        with self._lock:
            return copy.deepcopy([r for r in self._replays if r.topic == topic])

    def get_successful(self) -> List[DecisionReplay]:
        with self._lock:
            return copy.deepcopy([r for r in self._replays if r.outcome == "success"])

    def get_failed(self) -> List[DecisionReplay]:
        with self._lock:
            return copy.deepcopy([r for r in self._replays if r.outcome == "failure"])

    def get_common_paths(self) -> List[Dict]:
        with self._lock:
            paths: Dict[str, int] = {}
            for replay in self._replays:
                path = replay.get_path()
                paths[path] = paths.get(path, 0) + 1
            return [
                {"path": path, "count": count}
                for path, count in sorted(paths.items(), key=lambda item: -item[1])
            ]

    def count(self) -> int:
        with self._lock:
            return len(self._replays)

    def to_dict(self) -> Dict:
        with self._lock:
            recent = [replay.to_dict() for replay in self._replays[-10:]]
            paths: Dict[str, int] = {}
            for replay in self._replays:
                path = replay.get_path()
                paths[path] = paths.get(path, 0) + 1
            common_paths = [
                {"path": path, "count": count}
                for path, count in sorted(paths.items(), key=lambda item: -item[1])
            ]
            return {
                "count": len(self._replays),
                "replays": recent,
                "common_paths": common_paths,
            }
