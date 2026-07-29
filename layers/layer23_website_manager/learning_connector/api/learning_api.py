"""LearningAPI — Unified interface for Dashboard and other layers."""
from __future__ import annotations
from typing import Any, Dict


class LearningAPI:
    """Provide controlled access to learning engine internals."""

    def __init__(self, parent: Any) -> None:
        self._parent = parent

    def get_status(self) -> Dict[str, Any]:
        return {
            "collector": self._parent.collector.get_stats(),
            "analyzer": self._parent.analyzer.get_stats(),
            "mistakes": self._parent.mistakes.get_stats(),
            "strategy": self._parent.strategy.get_stats(),
            "prompts": self._parent.prompts.get_stats(),
            "decisions": self._parent.decisions.get_stats(),
            "patterns": self._parent.patterns.get_stats(),
            "knowledge": self._parent.knowledge.get_stats(),
            "recommendations": self._parent.recommendations.get_stats(),
            "improvements": self._parent.improvements.get_stats(),
            "versions": self._parent.versions.get_stats(),
            "memory": self._parent.memory.get_stats(),
        }

    def get_learning_summary(self) -> Dict[str, Any]:
        c = self._parent.collector.get_stats()
        a = self._parent.analyzer.get_stats()
        m = self._parent.mistakes.get_stats()
        r = self._parent.recommendations.get_stats()
        i = self._parent.improvements.get_stats()
        return {
            "total_events": c["total_events"],
            "success_rate": c["success_rate"],
            "total_metrics": a["total_metrics"],
            "total_mistakes": m["total_mistakes"],
            "unresolved_mistakes": m["unresolved"],
            "recommendations_pending": r["pending"],
            "improvements_made": i["total_actions"],
            "improvement_success_rate": i["success_rate"],
            "current_version": self._parent.versions.get_current_version(),
        }

    def run_learning_cycle(self) -> Dict[str, Any]:
        return self._parent.run_learning_cycle()
