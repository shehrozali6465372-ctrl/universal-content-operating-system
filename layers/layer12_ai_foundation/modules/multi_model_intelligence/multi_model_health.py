"""MultiModelHealth — health monitoring for multi-model system."""
from __future__ import annotations

import time
from typing import Any, Dict, List


class MultiModelHealth:
    """Health monitoring for multi-model intelligence."""

    def __init__(self) -> None:
        self._checks: Dict[str, Dict[str, Any]] = {}
        self._start_time = time.time()

    def check_model(self, model: str, is_healthy: bool = True,
                    latency_ms: float = 0.0) -> Dict[str, Any]:
        self._checks[model] = {
            "healthy": is_healthy,
            "latency_ms": latency_ms,
            "last_check": time.time(),
        }
        return self._checks[model]

    def get_model_health(self, model: str) -> Dict[str, Any]:
        return self._checks.get(model, {"healthy": False, "latency_ms": 0})

    def is_model_healthy(self, model: str) -> bool:
        check = self._checks.get(model)
        if check is None:
            return True  # Default to healthy if never checked
        return check["healthy"]

    def get_healthy_models(self) -> List[str]:
        return [m for m, c in self._checks.items() if c["healthy"]]

    def get_unhealthy_models(self) -> List[str]:
        return [m for m, c in self._checks.items() if not c["healthy"]]

    def overall_health(self) -> Dict[str, Any]:
        total = len(self._checks)
        healthy = sum(1 for c in self._checks.values() if c["healthy"])
        uptime = time.time() - self._start_time
        return {
            "total_models": total,
            "healthy": healthy,
            "unhealthy": total - healthy,
            "health_ratio": healthy / max(total, 1),
            "uptime_seconds": round(uptime, 2),
        }

    def to_dict(self) -> Dict[str, Any]:
        return self.overall_health()
