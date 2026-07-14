"""Decision Replay - Records and replays decision sequences."""
from __future__ import annotations
import time
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

    def __init__(self, topic: str = "", replay_id: str = "") -> None:
        self.topic = topic
        self.replay_id = replay_id
        self.steps: List[ReplayStep] = []
        self.final_decision = ""
        self.final_confidence = 0.0
        self.outcome = "pending"
        self.created_at = time.time()

    def add_step(self, stage: str, decision: str = "", confidence: float = 0.0,
                 input_data: Optional[Dict] = None, output_data: Optional[Dict] = None,
                 duration_ms: float = 0.0) -> ReplayStep:
        step = ReplayStep(len(self.steps) + 1, stage)
        step.decision = decision
        step.confidence = confidence
        step.input_data = input_data or {}
        step.output_data = output_data or {}
        step.duration_ms = duration_ms
        self.steps.append(step)
        return step

    def finalize(self, decision: str, confidence: float) -> None:
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
        self._replays: List[DecisionReplay] = []
        self._max = max_replays

    def record(self, replay: DecisionReplay) -> None:
        self._replays.append(replay)
        if len(self._replays) > self._max:
            self._replays = self._replays[-self._max:]

    def get_by_topic(self, topic: str) -> List[DecisionReplay]:
        return [r for r in self._replays if r.topic == topic]

    def get_successful(self) -> List[DecisionReplay]:
        return [r for r in self._replays if r.outcome == "success"]

    def get_failed(self) -> List[DecisionReplay]:
        return [r for r in self._replays if r.outcome == "failure"]

    def get_common_paths(self) -> List[Dict]:
        paths: Dict[str, int] = {}
        for r in self._replays:
            path = r.get_path()
            paths[path] = paths.get(path, 0) + 1
        return [{"path": p, "count": c} for p, c in sorted(paths.items(), key=lambda x: -x[1])]

    def count(self) -> int:
        return len(self._replays)

    def to_dict(self) -> Dict:
        return {
            "count": self.count(),
            "replays": [r.to_dict() for r in self._replays[-10:]],
            "common_paths": self.get_common_paths(),
        }
