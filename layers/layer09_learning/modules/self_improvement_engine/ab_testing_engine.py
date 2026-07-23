"""ABTestingEngine — A/B tests for titles, thumbnails, affiliate placements, CTAs, timing."""
from __future__ import annotations
import threading
import time
import uuid
from typing import Any, Dict, List, Optional


class ABVariant:
    __slots__ = ("id", "name", "content", "impressions", "clicks",
                 "conversions", "revenue", "ctr", "conversion_rate", "score")

    def __init__(self, name: str, content: str = "") -> None:
        self.id = str(uuid.uuid4())[:8]
        self.name = name
        self.content = content
        self.impressions = 0
        self.clicks = 0
        self.conversions = 0
        self.revenue = 0.0
        self.ctr = 0.0
        self.conversion_rate = 0.0
        self.score = 0.0

    @property
    def is_winner(self) -> bool:
        return self.score > 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id, "name": self.name, "content": self.content[:100],
            "impressions": self.impressions, "clicks": self.clicks,
            "conversions": self.conversions, "revenue": round(self.revenue, 2),
            "ctr": round(self.ctr, 2), "conversion_rate": round(self.conversion_rate, 2),
            "score": round(self.score, 1),
        }


class ABExperiment:
    __slots__ = ("id", "name", "test_type", "variants", "status",
                 "winner_id", "confidence", "min_samples", "created_at",
                 "ended_at", "duration_hours", "platform", "niche")

    TEST_TYPES = ("title", "thumbnail", "affiliate_placement", "cta_style",
                  "posting_time", "content_format", "hashtag_set", "hook_style")

    def __init__(self, name: str, test_type: str = "title",
                 platform: str = "", niche: str = "") -> None:
        self.id = str(uuid.uuid4())[:12]
        self.name = name
        self.test_type = test_type
        self.variants: List[ABVariant] = []
        self.status = "running"
        self.winner_id = ""
        self.confidence = 0.0
        self.min_samples = 100
        self.created_at = time.time()
        self.ended_at = 0.0
        self.duration_hours = 0.0
        self.platform = platform
        self.niche = niche

    @property
    def total_impressions(self) -> int:
        return sum(v.impressions for v in self.variants)

    @property
    def has_enough_data(self) -> bool:
        return self.total_impressions >= self.min_samples

    def get_winner(self) -> Optional[ABVariant]:
        for v in self.variants:
            if v.id == self.winner_id:
                return v
        return max(self.variants, key=lambda v: v.score) if self.variants else None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id, "name": self.name, "type": self.test_type,
            "status": self.status, "variants": len(self.variants),
            "total_impressions": self.total_impressions,
            "confidence": round(self.confidence, 1),
            "winner": self.get_winner().to_dict() if self.get_winner() else None,
            "platform": self.platform, "niche": self.niche,
        }


class ABTestingEngine:
    """Manages A/B tests across titles, thumbnails, CTAs, affiliate placements, timing."""
    _instance: Optional["ABTestingEngine"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "ABTestingEngine":
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
        self._experiments: Dict[str, ABExperiment] = {}
        self._type_index: Dict[str, List[str]] = {}
        self._completed_experiments: List[Dict[str, Any]] = []

    def create_experiment(self, name: str, test_type: str = "title",
                          variants: List[Dict[str, str]] = None,
                          platform: str = "", niche: str = "",
                          min_samples: int = 100) -> ABExperiment:
        exp = ABExperiment(name, test_type, platform, niche)
        exp.min_samples = min_samples
        if variants:
            for v in variants:
                av = ABVariant(v.get("name", ""), v.get("content", ""))
                exp.variants.append(av)
        self._experiments[exp.id] = exp
        self._type_index.setdefault(test_type, []).append(exp.id)
        return exp

    def add_variant(self, experiment_id: str, name: str,
                    content: str = "") -> Optional[ABVariant]:
        exp = self._experiments.get(experiment_id)
        if exp:
            av = ABVariant(name, content)
            exp.variants.append(av)
            return av
        return None

    def record_impression(self, experiment_id: str, variant_id: str) -> bool:
        exp = self._experiments.get(experiment_id)
        if not exp:
            return False
        for v in exp.variants:
            if v.id == variant_id:
                v.impressions += 1
                v.ctr = (v.clicks / v.impressions * 100) if v.impressions > 0 else 0
                v.conversion_rate = (v.conversions / v.clicks * 100) if v.clicks > 0 else 0
                return True
        return False

    def record_click(self, experiment_id: str, variant_id: str) -> bool:
        exp = self._experiments.get(experiment_id)
        if not exp:
            return False
        for v in exp.variants:
            if v.id == variant_id:
                v.clicks += 1
                v.ctr = (v.clicks / v.impressions * 100) if v.impressions > 0 else 0
                return True
        return False

    def record_conversion(self, experiment_id: str, variant_id: str,
                          revenue: float = 0.0) -> bool:
        exp = self._experiments.get(experiment_id)
        if not exp:
            return False
        for v in exp.variants:
            if v.id == variant_id:
                v.conversions += 1
                v.revenue += revenue
                v.conversion_rate = (v.conversions / v.clicks * 100) if v.clicks > 0 else 0
                return True
        return False

    def evaluate_experiment(self, experiment_id: str) -> Optional[ABExperiment]:
        exp = self._experiments.get(experiment_id)
        if not exp or not exp.has_enough_data:
            return None
        for v in exp.variants:
            v.score = (v.ctr * 0.4 + v.conversion_rate * 0.4 +
                       min(v.revenue / max(v.impressions, 1) * 100, 1.0) * 0.2) * 100
        winner = max(exp.variants, key=lambda v: v.score)
        exp.winner_id = winner.id
        exp.confidence = min(exp.total_impressions / (exp.min_samples * 2) * 100, 99.0)
        return exp

    def conclude_experiment(self, experiment_id: str) -> bool:
        exp = self._experiments.get(experiment_id)
        if exp and exp.status == "running":
            self.evaluate_experiment(experiment_id)
            exp.status = "completed"
            exp.ended_at = time.time()
            exp.duration_hours = (exp.ended_at - exp.created_at) / 3600
            self._completed_experiments.append(exp.to_dict())
            return True
        return False

    def get_experiment(self, eid: str) -> Optional[ABExperiment]:
        return self._experiments.get(eid)

    def get_running(self, test_type: str = "") -> List[ABExperiment]:
        exps = [e for e in self._experiments.values() if e.status == "running"]
        if test_type:
            exps = [e for e in exps if e.test_type == test_type]
        return exps

    def get_winners(self) -> List[ABExperiment]:
        return [e for e in self._experiments.values()
                if e.status == "completed" and e.winner_id]

    def get_testing_status(self) -> Dict[str, Any]:
        exps = list(self._experiments.values())
        return {
            "total_experiments": len(exps),
            "running": sum(1 for e in exps if e.status == "running"),
            "completed": sum(1 for e in exps if e.status == "completed"),
            "by_type": {t: len(ids) for t, ids in self._type_index.items()},
            "total_impressions": sum(e.total_impressions for e in exps),
            "total_winners": len(self.get_winners()),
        }

    def stats(self) -> Dict[str, Any]:
        return {
            "experiments": len(self._experiments),
            "types": len(self._type_index),
            "completed": len(self._completed_experiments),
        }


def get_ab_testing_engine() -> ABTestingEngine:
    return ABTestingEngine()
