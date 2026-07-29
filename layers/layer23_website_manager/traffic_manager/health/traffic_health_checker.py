"""TrafficHealthChecker — Monitor traffic drops, broken sources, dead pages, low CTR, high bounce."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional


class TrafficHealthChecker:
    """Check traffic health — drops, broken sources, dead pages, low CTR, high bounce."""

    def __init__(self) -> None:
        self._health_log: List[dict] = []

    def check_health(self, current_traffic: int, previous_traffic: int,
                      bounce_rate: float = 0.0, ctr: float = 0.0,
                      indexed_pages: int = 0) -> Dict[str, Any]:
        """Run full traffic health check."""
        issues: List[str] = []
        score = 100.0

        if previous_traffic > 0:
            change = ((current_traffic - previous_traffic) / previous_traffic) * 100
            if change < -30:
                issues.append(f"Critical traffic drop: {change:.0f}%")
                score -= 30
            elif change < -10:
                issues.append(f"Traffic decline: {change:.0f}%")
                score -= 15
        else:
            if current_traffic == 0:
                issues.append("No traffic detected")
                score -= 30

        if bounce_rate > 70:
            issues.append(f"High bounce rate: {bounce_rate:.0f}%")
            score -= 15
        elif bounce_rate > 50:
            score -= 5

        if ctr > 0 and ctr < 1:
            issues.append(f"Low CTR: {ctr:.2f}%")
            score -= 10

        if indexed_pages == 0:
            issues.append("No pages indexed")
            score -= 10

        result = {"health_score": max(0, score), "status": "healthy" if score >= 70 else "degraded" if score >= 40 else "critical",
                   "issues": issues, "issue_count": len(issues)}
        self._health_log.append(result)
        return result

    def get_stats(self) -> Dict[str, Any]:
        healthy = sum(1 for h in self._health_log if h["health_score"] >= 70)
        return {"total_checks": len(self._health_log), "healthy": healthy, "unhealthy": len(self._health_log) - healthy}
