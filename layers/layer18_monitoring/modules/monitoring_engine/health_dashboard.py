"""Thread-safe aggregated component health dashboard."""
from __future__ import annotations

import threading
import time
from typing import Any, Dict, List, Optional


class HealthDashboard:
    def __init__(self, history_size: int = 1000) -> None:
        if history_size <= 0:
            raise ValueError("history_size must be positive")
        self._lock = threading.RLock()
        self._history_size = history_size
        self._components: Dict[str, Dict[str, Any]] = {}
        self._history: List[Dict[str, Any]] = []

    def update_component(
        self,
        name: str,
        score: int,
        status: str = "healthy",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        if not name.strip() or status not in {"healthy", "degraded", "unhealthy"}:
            raise ValueError("invalid component")
        with self._lock:
            self._components[name] = {
                "name": name,
                "score": max(0, min(100, int(score))),
                "status": status,
                "last_check": time.time(),
                "details": dict(details or {}),
            }

    def get_component_health(self, name: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            component = self._components.get(name)
            return dict(component) if component else None

    def get_overall_health(self) -> Dict[str, Any]:
        with self._lock:
            components = {
                key: dict(value) for key, value in self._components.items()
            }
        if not components:
            return {
                "score": 0,
                "status": "unknown",
                "component_count": 0,
                "components": {},
            }

        score = round(
            sum(component["score"] for component in components.values())
            / len(components)
        )
        statuses = [component["status"] for component in components.values()]
        status = (
            "unhealthy"
            if "unhealthy" in statuses
            else "degraded"
            if "degraded" in statuses
            else "healthy"
        )
        result = {
            "score": score,
            "status": status,
            "component_count": len(components),
            "components": {
                key: {"score": value["score"], "status": value["status"]}
                for key, value in components.items()
            },
        }
        with self._lock:
            self._history.append(
                {
                    "timestamp": time.time(),
                    "score": score,
                    "status": status,
                    "component_count": len(components),
                }
            )
            if len(self._history) > self._history_size:
                del self._history[:-self._history_size]
        return result

    def get_health_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        if limit <= 0:
            raise ValueError("limit must be positive")
        with self._lock:
            return [dict(item) for item in self._history[-limit:]]

    def get_unhealthy_components(self) -> List[Dict[str, Any]]:
        with self._lock:
            return [
                dict(component)
                for component in self._components.values()
                if component["status"] in {"unhealthy", "degraded"}
            ]

    def get_score_trend(self, window: int = 20) -> Dict[str, Any]:
        if window <= 0:
            raise ValueError("window must be positive")
        with self._lock:
            recent = list(self._history[-window:])
        if len(recent) < 2:
            return {
                "trend": "stable",
                "scores": [item["score"] for item in recent],
            }
        scores = [item["score"] for item in recent]
        midpoint = len(scores) // 2
        first = sum(scores[:midpoint]) / midpoint
        second = sum(scores[midpoint:]) / (len(scores) - midpoint)
        diff = second - first
        return {
            "trend": (
                "improving" if diff > 5 else "declining" if diff < -5 else "stable"
            ),
            "avg_first": round(first, 1),
            "avg_second": round(second, 1),
            "scores": scores,
        }

    def stats(self) -> Dict[str, Any]:
        with self._lock:
            components = list(self._components.values())
            return {
                "total_components": len(components),
                "healthy": sum(item["status"] == "healthy" for item in components),
                "degraded": sum(item["status"] == "degraded" for item in components),
                "unhealthy": sum(item["status"] == "unhealthy" for item in components),
                "history_size": len(self._history),
            }
