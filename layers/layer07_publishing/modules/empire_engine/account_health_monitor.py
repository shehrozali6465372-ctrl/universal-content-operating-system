"""AccountHealthMonitor — Posting frequency, errors, shadow-ban, growth metrics."""
from __future__ import annotations
import threading
import time
from typing import Any, Dict, List, Optional


class HealthMetric:
    __slots__ = ("account_id", "platform", "posting_frequency", "avg_engagement",
                 "follower_growth_rate", "error_count", "warning_count",
                 "shadow_ban_score", "health_score", "last_checked",
                 "issues", "metrics_history")

    def __init__(self, account_id: str, platform: str = "") -> None:
        self.account_id = account_id
        self.platform = platform
        self.posting_frequency = 0.0
        self.avg_engagement = 0.0
        self.follower_growth_rate = 0.0
        self.error_count = 0
        self.warning_count = 0
        self.shadow_ban_score = 0.0
        self.health_score = 100.0
        self.last_checked = time.time()
        self.issues: List[str] = []
        self.metrics_history: List[Dict[str, Any]] = []

    @property
    def status(self) -> str:
        if self.health_score >= 80:
            return "healthy"
        elif self.health_score >= 50:
            return "degraded"
        return "unhealthy"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "account_id": self.account_id, "platform": self.platform,
            "posting_frequency": round(self.posting_frequency, 1),
            "avg_engagement": round(self.avg_engagement, 2),
            "follower_growth": round(self.follower_growth_rate, 2),
            "errors": self.error_count, "warnings": self.warning_count,
            "shadow_ban_score": round(self.shadow_ban_score, 1),
            "health_score": round(self.health_score, 1),
            "status": self.status, "issues": self.issues,
        }


class AccountHealthMonitor:
    """Monitors account health: frequency, errors, shadow-ban, growth."""
    _instance: Optional["AccountHealthMonitor"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "AccountHealthMonitor":
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
        self._metrics: Dict[str, HealthMetric] = {}
        self._alerts: List[Dict[str, Any]] = []
        self._check_history: List[Dict[str, Any]] = []

    def check_account(self, account_id: str, platform: str = "",
                      posting_frequency: float = 0.0, avg_engagement: float = 0.0,
                      follower_growth: float = 0.0, error_count: int = 0,
                      warning_count: int = 0) -> HealthMetric:
        hm = HealthMetric(account_id, platform)
        hm.posting_frequency = posting_frequency
        hm.avg_engagement = avg_engagement
        hm.follower_growth_rate = follower_growth
        hm.error_count = error_count
        hm.warning_count = warning_count
        hm.health_score = self._calculate_health(hm)
        hm.issues = self._detect_issues(hm)
        hm.shadow_ban_score = self._detect_shadow_ban(hm)
        self._metrics[account_id] = hm
        self._check_history.append({
            "account_id": account_id, "score": hm.health_score,
            "timestamp": time.time(),
        })
        if hm.health_score < 50:
            self._alerts.append({
                "account_id": account_id, "score": hm.health_score,
                "issues": hm.issues, "timestamp": time.time(),
            })
        return hm

    def _calculate_health(self, hm: HealthMetric) -> float:
        score = 100.0
        if hm.error_count > 0:
            score -= min(hm.error_count * 10, 30)
        if hm.warning_count > 0:
            score -= min(hm.warning_count * 5, 15)
        if hm.posting_frequency < 0.1:
            score -= 15
        if hm.avg_engagement < 0.5:
            score -= 10
        if hm.follower_growth_rate < 0:
            score -= 10
        if hm.shadow_ban_score > 50:
            score -= 20
        return max(0, min(100, score))

    def _detect_issues(self, hm: HealthMetric) -> List[str]:
        issues = []
        if hm.error_count > 5:
            issues.append("High error rate detected")
        if hm.posting_frequency < 0.1:
            issues.append("Very low posting frequency")
        if hm.avg_engagement < 0.5:
            issues.append("Low engagement rate")
        if hm.follower_growth_rate < -5:
            issues.append("Losing followers")
        if hm.warning_count > 3:
            issues.append("Multiple warnings from platform")
        return issues

    def _detect_shadow_ban(self, hm: HealthMetric) -> float:
        score = 0.0
        if hm.avg_engagement < 0.1 and hm.posting_frequency > 0:
            score += 40
        if hm.follower_growth_rate < -10:
            score += 30
        if hm.error_count > 10:
            score += 20
        return min(score, 100.0)

    def get_health(self, account_id: str) -> Optional[HealthMetric]:
        return self._metrics.get(account_id)

    def get_unhealthy_accounts(self) -> List[HealthMetric]:
        return [h for h in self._metrics.values() if h.health_score < 50]

    def get_shadow_ban_suspects(self) -> List[HealthMetric]:
        return [h for h in self._metrics.values() if h.shadow_ban_score >= 50]

    def get_health_summary(self) -> Dict[str, Any]:
        metrics = list(self._metrics.values())
        return {
            "total_checked": len(metrics),
            "healthy": sum(1 for m in metrics if m.health_score >= 80),
            "degraded": sum(1 for m in metrics if 50 <= m.health_score < 80),
            "unhealthy": sum(1 for m in metrics if m.health_score < 50),
            "shadow_ban_suspects": len(self.get_shadow_ban_suspects()),
            "total_errors": sum(m.error_count for m in metrics),
            "total_warnings": sum(m.warning_count for m in metrics),
            "avg_health_score": round(
                sum(m.health_score for m in metrics) / len(metrics), 1
            ) if metrics else 0,
            "active_alerts": len(self._alerts),
        }

    def stats(self) -> Dict[str, Any]:
        return {
            "checked": len(self._metrics),
            "alerts": len(self._alerts),
            "checks": len(self._check_history),
        }


def get_account_health_monitor() -> AccountHealthMonitor:
    return AccountHealthMonitor()
