"""HealthDashboard — Aggregated health scores for all system components.

Features:
- Per-component health scoring (0-100)
- Overall system health score
- Component dependency mapping
- Health history tracking
- Status indicators (healthy, degraded, unhealthy)
"""
from __future__ import annotations
import time
import threading
from typing import Any, Dict, List, Optional


class HealthDashboard:
    """Aggregated health monitoring dashboard."""

    def __init__(self):
        self._lock = threading.Lock()
        self._components: Dict[str, Dict[str, Any]] = {}
        self._history: List[Dict[str, Any]] = []

        # Default components
        self._default_components = [
            "database", "redis", "vector_db", "publishing",
            "monitoring", "ai_engine", "scheduler",
        ]

    def update_component(self, name: str, score: int, status: str = "healthy",
                         details: Dict[str, Any] = None) -> None:
        """Update health for a component.

        Args:
            name: Component name
            score: Health score 0-100
            status: healthy, degraded, unhealthy
            details: Additional details
        """
        with self._lock:
            self._components[name] = {
                "name": name,
                "score": max(0, min(100, score)),
                "status": status,
                "last_check": time.time(),
                "details": details or {},
            }

    def get_component_health(self, name: str) -> Optional[Dict[str, Any]]:
        """Get health for a specific component."""
        return self._components.get(name)

    def get_overall_health(self) -> Dict[str, Any]:
        """Get overall system health."""
        with self._lock:
            components = dict(self._components)

        if not components:
            return {"score": 0, "status": "unknown", "components": {}}

        # Calculate weighted average
        total_score = 0
        count = 0
        statuses = []
        for name, comp in components.items():
            total_score += comp["score"]
            count += 1
            statuses.append(comp["status"])

        avg_score = total_score // count if count > 0 else 0

        # Determine overall status
        if "unhealthy" in statuses:
            overall_status = "degraded"
        elif all(s == "healthy" for s in statuses):
            overall_status = "healthy"
        else:
            overall_status = "degraded"

        # Record in history
        with self._lock:
            self._history.append({
                "timestamp": time.time(),
                "score": avg_score,
                "status": overall_status,
                "component_count": count,
            })
            if len(self._history) > 1000:
                self._history = self._history[-500:]

        return {
            "score": avg_score,
            "status": overall_status,
            "component_count": count,
            "components": {name: {"score": c["score"], "status": c["status"]}
                           for name, c in components.items()},
        }

    def get_health_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get health score history."""
        with self._lock:
            return list(self._history[-limit:])

    def get_unhealthy_components(self) -> List[Dict[str, Any]]:
        """Get all unhealthy or degraded components."""
        with self._lock:
            return [
                comp for comp in self._components.values()
                if comp["status"] in ("unhealthy", "degraded")
            ]

    def get_score_trend(self, window: int = 20) -> Dict[str, Any]:
        """Analyze health score trend."""
        with self._lock:
            recent = self._history[-window:]

        if len(recent) < 2:
            return {"trend": "stable", "scores": [h["score"] for h in recent]}

        scores = [h["score"] for h in recent]
        avg_first = sum(scores[:len(scores)//2]) / max(1, len(scores)//2)
        avg_second = sum(scores[len(scores)//2:]) / max(1, len(scores) - len(scores)//2)

        diff = avg_second - avg_first
        if diff > 5:
            trend = "improving"
        elif diff < -5:
            trend = "declining"
        else:
            trend = "stable"

        return {"trend": trend, "avg_first": round(avg_first, 1),
                "avg_second": round(avg_second, 1), "scores": scores}

    def stats(self) -> Dict[str, Any]:
        """Get dashboard statistics."""
        with self._lock:
            components = dict(self._components)

        healthy = sum(1 for c in components.values() if c["status"] == "healthy")
        degraded = sum(1 for c in components.values() if c["status"] == "degraded")
        unhealthy = sum(1 for c in components.values() if c["status"] == "unhealthy")

        return {
            "total_components": len(components),
            "healthy": healthy,
            "degraded": degraded,
            "unhealthy": unhealthy,
            "history_size": len(self._history),
        }
