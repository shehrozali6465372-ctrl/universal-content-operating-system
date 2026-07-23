"""PromptOptimizer — Auto-improves AI prompts: promotes winners, replaces losers."""
from __future__ import annotations
import threading
import time
import uuid
from typing import Any, Dict, List, Optional


class PromptVersion:
    __slots__ = ("id", "prompt_text", "category", "version", "uses",
                 "successes", "failures", "avg_quality_score", "avg_engagement",
                 "status", "created_at", "parent_id", "tags")

    def __init__(self, prompt_text: str, category: str = "content",
                 version: int = 1) -> None:
        self.id = str(uuid.uuid4())[:12]
        self.prompt_text = prompt_text
        self.category = category
        self.version = version
        self.uses = 0
        self.successes = 0
        self.failures = 0
        self.avg_quality_score = 0.0
        self.avg_engagement = 0.0
        self.status = "active"
        self.created_at = time.time()
        self.parent_id = ""
        self.tags: List[str] = []

    @property
    def success_rate(self) -> float:
        return (self.successes / self.uses * 100) if self.uses > 0 else 0.0

    @property
    def score(self) -> float:
        sr = min(self.success_rate / 100, 1.0) * 40
        qs = min(self.avg_quality_score / 10, 1.0) * 35
        eg = min(self.avg_engagement / 10, 1.0) * 25
        return sr + qs + eg

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id, "prompt": self.prompt_text[:100],
            "category": self.category, "version": self.version,
            "uses": self.uses, "successes": self.successes,
            "failures": self.failures,
            "success_rate": round(self.success_rate, 1),
            "quality": round(self.avg_quality_score, 1),
            "engagement": round(self.avg_engagement, 1),
            "score": round(self.score, 1), "status": self.status,
        }


class PromptOptimizer:
    """Manages, scores, and auto-evolves AI prompts for better results."""
    _instance: Optional["PromptOptimizer"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "PromptOptimizer":
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
        self._prompts: Dict[str, PromptVersion] = {}
        self._category_index: Dict[str, List[str]] = {}
        self._evolution_log: List[Dict[str, Any]] = []

    def add_prompt(self, text: str, category: str = "content",
                   tags: List[str] = None) -> PromptVersion:
        pv = PromptVersion(text, category)
        if tags:
            pv.tags = tags
        self._prompts[pv.id] = pv
        self._category_index.setdefault(category, []).append(pv.id)
        return pv

    def get_prompt(self, pid: str) -> Optional[PromptVersion]:
        return self._prompts.get(pid)

    def record_use(self, prompt_id: str, success: bool = True,
                   quality_score: float = 5.0, engagement: float = 3.0) -> bool:
        pv = self._prompts.get(prompt_id)
        if not pv:
            return False
        pv.uses += 1
        if success:
            pv.successes += 1
        else:
            pv.failures += 1
        n = pv.uses
        pv.avg_quality_score = ((pv.avg_quality_score * (n - 1) + quality_score) / n)
        pv.avg_engagement = ((pv.avg_engagement * (n - 1) + engagement) / n)
        return True

    def get_best_prompts(self, category: str = "", limit: int = 10) -> List[PromptVersion]:
        prompts = list(self._prompts.values())
        if category:
            prompts = [p for p in prompts if p.category == category]
        return sorted(prompts, key=lambda p: p.score, reverse=True)[:limit]

    def get_worst_prompts(self, min_uses: int = 3, limit: int = 10) -> List[PromptVersion]:
        return sorted(
            [p for p in self._prompts.values() if p.uses >= min_uses],
            key=lambda p: p.score,
        )[:limit]

    def promote_prompt(self, prompt_id: str) -> bool:
        pv = self._prompts.get(prompt_id)
        if pv:
            pv.status = "promoted"
            self._evolution_log.append({
                "action": "promote", "prompt_id": prompt_id,
                "score": pv.score, "timestamp": time.time(),
            })
            return True
        return False

    def retire_prompt(self, prompt_id: str) -> bool:
        pv = self._prompts.get(prompt_id)
        if pv:
            pv.status = "retired"
            self._evolution_log.append({
                "action": "retire", "prompt_id": prompt_id,
                "score": pv.score, "timestamp": time.time(),
            })
            return True
        return False

    def evolve_prompt(self, parent_id: str, new_text: str) -> Optional[PromptVersion]:
        parent = self._prompts.get(parent_id)
        if not parent:
            return None
        new_pv = PromptVersion(new_text, parent.category, parent.version + 1)
        new_pv.parent_id = parent_id
        new_pv.tags = parent.tags.copy()
        self._prompts[new_pv.id] = new_pv
        self._category_index.setdefault(parent.category, []).append(new_pv.id)
        parent.status = "superseded"
        self._evolution_log.append({
            "action": "evolve", "parent": parent_id,
            "child": new_pv.id, "timestamp": time.time(),
        })
        return new_pv

    def get_optimization_report(self) -> Dict[str, Any]:
        prompts = list(self._prompts.values())
        return {
            "total_prompts": len(prompts),
            "active": sum(1 for p in prompts if p.status == "active"),
            "promoted": sum(1 for p in prompts if p.status == "promoted"),
            "retired": sum(1 for p in prompts if p.status == "retired"),
            "superseded": sum(1 for p in prompts if p.status == "superseded"),
            "avg_score": round(
                sum(p.score for p in prompts) / len(prompts), 1
            ) if prompts else 0,
            "total_uses": sum(p.uses for p in prompts),
            "categories": {c: len(ids) for c, ids in self._category_index.items()},
            "best_5": [p.to_dict() for p in self.get_best_prompts(limit=5)],
            "worst_5": [p.to_dict() for p in self.get_worst_prompts(limit=5)],
        }

    def stats(self) -> Dict[str, Any]:
        return {
            "prompts": len(self._prompts),
            "categories": len(self._category_index),
            "evolutions": len(self._evolution_log),
        }


def get_prompt_optimizer() -> PromptOptimizer:
    return PromptOptimizer()
