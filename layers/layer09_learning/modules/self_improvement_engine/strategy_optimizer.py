"""StrategyOptimizer — Data-driven strategy recommendations for niches, platforms, content."""
from __future__ import annotations
import threading
import time
import uuid
from typing import Any, Dict, List, Optional


class StrategyRecommendation:
    __slots__ = ("id", "category", "action", "niche", "platform",
                 "priority", "expected_impact", "reason", "data_points",
                 "status", "created_at", "applied_at")

    def __init__(self, category: str, action: str, niche: str = "",
                 platform: str = "", priority: int = 5) -> None:
        self.id = str(uuid.uuid4())[:12]
        self.category = category
        self.action = action
        self.niche = niche
        self.platform = platform
        self.priority = priority
        self.expected_impact = 0.0
        self.reason = ""
        self.data_points = 0
        self.status = "pending"
        self.created_at = time.time()
        self.applied_at = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id, "category": self.category,
            "action": self.action, "niche": self.niche,
            "platform": self.platform, "priority": self.priority,
            "impact": round(self.expected_impact, 1),
            "reason": self.reason, "status": self.status,
        }


class StrategyVersion:
    __slots__ = ("id", "version", "name", "config", "performance_score",
                 "created_at", "status", "parent_id")

    def __init__(self, version: str, name: str, config: Dict[str, Any]) -> None:
        self.id = str(uuid.uuid4())[:12]
        self.version = version
        self.name = name
        self.config = config
        self.performance_score = 0.0
        self.created_at = time.time()
        self.status = "draft"
        self.parent_id = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id, "version": self.version, "name": self.name,
            "score": round(self.performance_score, 1),
            "status": self.status, "parent": self.parent_id,
        }


class StrategyOptimizer:
    """Analyzes data and generates strategy recommendations."""
    _instance: Optional["StrategyOptimizer"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "StrategyOptimizer":
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
        self._recommendations: Dict[str, StrategyRecommendation] = {}
        self._versions: Dict[str, StrategyVersion] = {}
        self._current_version: Optional[str] = None
        self._strategy_history: List[Dict[str, Any]] = []

    def recommend(self, category: str, action: str, niche: str = "",
                  platform: str = "", priority: int = 5, impact: float = 0.0,
                  reason: str = "", data_points: int = 0) -> StrategyRecommendation:
        rec = StrategyRecommendation(category, action, niche, platform, priority)
        rec.expected_impact = impact
        rec.reason = reason
        rec.data_points = data_points
        self._recommendations[rec.id] = rec
        return rec

    def get_recommendation(self, rid: str) -> Optional[StrategyRecommendation]:
        return self._recommendations.get(rid)

    def get_pending(self, category: str = "") -> List[StrategyRecommendation]:
        recs = [r for r in self._recommendations.values() if r.status == "pending"]
        if category:
            recs = [r for r in recs if r.category == category]
        return sorted(recs, key=lambda r: r.priority, reverse=True)

    def apply_recommendation(self, rid: str) -> bool:
        rec = self._recommendations.get(rid)
        if rec and rec.status == "pending":
            rec.status = "applied"
            rec.applied_at = time.time()
            self._strategy_history.append({
                "action": "apply", "recommendation": rid,
                "timestamp": time.time(),
            })
            return True
        return False

    def dismiss_recommendation(self, rid: str) -> bool:
        rec = self._recommendations.get(rid)
        if rec:
            rec.status = "dismissed"
            return True
        return False

    def create_version(self, version: str, name: str,
                       config: Dict[str, Any]) -> StrategyVersion:
        sv = StrategyVersion(version, name, config)
        self._versions[sv.id] = sv
        return sv

    def activate_version(self, version_id: str) -> bool:
        sv = self._versions.get(version_id)
        if sv:
            if self._current_version:
                old = self._versions.get(self._current_version)
                if old:
                    old.status = "inactive"
            sv.status = "active"
            self._current_version = version_id
            return True
        return False

    def rollback_version(self) -> Optional[StrategyVersion]:
        if not self._current_version:
            return None
        current = self._versions.get(self._current_version)
        if current and current.parent_id:
            parent = self._versions.get(current.parent_id)
            if parent:
                current.status = "inactive"
                parent.status = "active"
                self._current_version = parent.id
                return parent
        versions = list(self._versions.values())
        active = [v for v in versions if v.status in ("active", "draft")]
        if len(active) > 1:
            active.sort(key=lambda v: v.created_at)
            current.status = "inactive"
            active[-1].status = "active"
            self._current_version = active[-1].id
            return active[-1]
        return None

    def get_current_version(self) -> Optional[StrategyVersion]:
        return self._versions.get(self._current_version) if self._current_version else None

    def get_all_versions(self) -> List[StrategyVersion]:
        return sorted(self._versions.values(), key=lambda v: v.created_at, reverse=True)

    def get_strategy_status(self) -> Dict[str, Any]:
        recs = list(self._recommendations.values())
        versions = list(self._versions.values())
        return {
            "total_recommendations": len(recs),
            "pending": sum(1 for r in recs if r.status == "pending"),
            "applied": sum(1 for r in recs if r.status == "applied"),
            "dismissed": sum(1 for r in recs if r.status == "dismissed"),
            "total_versions": len(versions),
            "current_version": self.get_current_version().to_dict() if self.get_current_version() else None,
            "history": len(self._strategy_history),
        }

    def stats(self) -> Dict[str, Any]:
        return {
            "recommendations": len(self._recommendations),
            "versions": len(self._versions),
            "history": len(self._strategy_history),
        }


def get_strategy_optimizer() -> StrategyOptimizer:
    return StrategyOptimizer()
