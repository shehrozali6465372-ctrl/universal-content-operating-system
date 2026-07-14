"""Confidence Evolution - Tracks confidence through pipeline stages."""
from __future__ import annotations
import time
from typing import Dict, List, Optional


class ConfidenceStage:
    """A single stage in the confidence pipeline."""
    __slots__ = ("stage_name", "confidence", "factors", "timestamp")

    def __init__(self, stage_name: str = "", confidence: float = 0.0,
                 factors: Optional[Dict[str, float]] = None):
        self.stage_name = stage_name
        self.confidence = confidence
        self.factors = factors or {}
        self.timestamp = time.time()

    def to_dict(self) -> Dict:
        return {
            "stage": self.stage_name, "confidence": round(self.confidence, 3),
            "factors": {k: round(v, 3) for k, v in self.factors.items()},
            "timestamp": self.timestamp,
        }


class ConfidenceEvolution:
    """Tracks how confidence evolves through decision pipeline stages."""

    def __init__(self, topic: str = "") -> None:
        self.topic = topic
        self.stages: List[ConfidenceStage] = []
        self.final_confidence = 0.0

    def add_stage(self, stage_name: str, confidence: float,
                  factors: Optional[Dict[str, float]] = None) -> None:
        self.stages.append(ConfidenceStage(stage_name, confidence, factors))
        self._recalculate()

    def _recalculate(self) -> None:
        if not self.stages:
            self.final_confidence = 0.0
            return
        # Weighted average with recency bias
        total = 0.0
        weight_sum = 0.0
        for i, stage in enumerate(self.stages):
            w = 1.0 + i * 0.1  # slight recency bias
            total += stage.confidence * w
            weight_sum += w
        self.final_confidence = total / weight_sum if weight_sum > 0 else 0.0

    def get_contribution(self, stage_name: str) -> float:
        for s in self.stages:
            if s.stage_name == stage_name:
                return s.confidence
        return 0.0

    def get_weakest_stage(self) -> Optional[ConfidenceStage]:
        if not self.stages:
            return None
        return min(self.stages, key=lambda s: s.confidence)

    def get_strongest_stage(self) -> Optional[ConfidenceStage]:
        if not self.stages:
            return None
        return max(self.stages, key=lambda s: s.confidence)

    def get_drops(self) -> List[Dict]:
        drops = []
        for i in range(1, len(self.stages)):
            prev = self.stages[i - 1]
            curr = self.stages[i]
            if curr.confidence < prev.confidence - 0.05:
                drops.append({
                    "from_stage": prev.stage_name,
                    "to_stage": curr.stage_name,
                    "drop": round(prev.confidence - curr.confidence, 3),
                })
        return drops

    def to_dict(self) -> Dict:
        return {
            "topic": self.topic,
            "stages": [s.to_dict() for s in self.stages],
            "final_confidence": round(self.final_confidence, 3),
            "weakest_stage": self.get_weakest_stage().stage_name if self.get_weakest_stage() else None,
            "drops": self.get_drops(),
        }


class ConfidenceEvolutionTracker:
    """Manages multiple topic confidence evolutions."""

    def __init__(self) -> None:
        self._evolutions: Dict[str, ConfidenceEvolution] = {}

    def create(self, topic: str) -> ConfidenceEvolution:
        evolution = ConfidenceEvolution(topic)
        self._evolutions[topic] = evolution
        return evolution

    def get(self, topic: str) -> Optional[ConfidenceEvolution]:
        return self._evolutions.get(topic)

    def add_stage(self, topic: str, stage: str, confidence: float,
                  factors: Optional[Dict[str, float]] = None) -> None:
        evo = self._evolutions.get(topic)
        if not evo:
            evo = self.create(topic)
        evo.add_stage(stage, confidence, factors)

    def get_all_topics(self) -> List[str]:
        return list(self._evolutions.keys())

    def get_final_confidence(self, topic: str) -> float:
        evo = self._evolutions.get(topic)
        return evo.final_confidence if evo else 0.0

    def to_dict(self) -> Dict:
        return {t: e.to_dict() for t, e in self._evolutions.items()}
