"""AlertCenter — Revenue drops, account issues, affiliate problems, API failures, security."""
from __future__ import annotations
import threading
import time
import uuid
from typing import Any, Dict, List, Optional


class Alert:
    __slots__ = ("id", "category", "severity", "title", "message",
                 "source", "status", "created_at", "acknowledged_at",
                 "resolved_at", "metadata")

    SEVERITIES = ("info", "warning", "critical", "emergency")
    CATEGORIES = ("revenue", "account", "affiliate", "api", "security", "system")

    def __init__(self, category: str, severity: str, title: str,
                 message: str = "", source: str = "") -> None:
        self.id = str(uuid.uuid4())[:12]
        self.category = category
        self.severity = severity
        self.title = title
        self.message = message
        self.source = source
        self.status = "active"
        self.created_at = time.time()
        self.acknowledged_at = 0.0
        self.resolved_at = 0.0
        self.metadata: Dict[str, Any] = {}

    @property
    def age_minutes(self) -> float:
        return (time.time() - self.created_at) / 60

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id, "category": self.category,
            "severity": self.severity, "title": self.title,
            "message": self.message, "source": self.source,
            "status": self.status,
            "age_minutes": round(self.age_minutes, 1),
        }


class AlertCenter:
    """Central alert system for all business and system issues."""
    _instance: Optional["AlertCenter"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "AlertCenter":
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
        self._alerts: Dict[str, Alert] = {}
        self._category_index: Dict[str, List[str]] = {}
        self._severity_index: Dict[str, List[str]] = {}
        self._alert_history: List[Dict[str, Any]] = []

    def fire(self, category: str, severity: str, title: str,
             message: str = "", source: str = "") -> Alert:
        alert = Alert(category, severity, title, message, source)
        self._alerts[alert.id] = alert
        self._category_index.setdefault(category, []).append(alert.id)
        self._severity_index.setdefault(severity, []).append(alert.id)
        self._alert_history.append(alert.to_dict())
        return alert

    def acknowledge(self, alert_id: str) -> bool:
        a = self._alerts.get(alert_id)
        if a and a.status == "active":
            a.status = "acknowledged"
            a.acknowledged_at = time.time()
            return True
        return False

    def resolve(self, alert_id: str) -> bool:
        a = self._alerts.get(alert_id)
        if a and a.status in ("active", "acknowledged"):
            a.status = "resolved"
            a.resolved_at = time.time()
            return True
        return False

    def get_active(self, category: str = "", severity: str = "") -> List[Alert]:
        alerts = [a for a in self._alerts.values() if a.status == "active"]
        if category:
            alerts = [a for a in alerts if a.category == category]
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        return sorted(alerts, key=lambda a: (
            {"emergency": 0, "critical": 1, "warning": 2, "info": 3}.get(a.severity, 4),
            -a.created_at,
        ))

    def get_critical(self) -> List[Alert]:
        return self.get_active(severity="critical") + self.get_active(severity="emergency")

    def get_alert_summary(self) -> Dict[str, Any]:
        alerts = list(self._alerts.values())
        return {
            "total": len(alerts),
            "active": sum(1 for a in alerts if a.status == "active"),
            "acknowledged": sum(1 for a in alerts if a.status == "acknowledged"),
            "resolved": sum(1 for a in alerts if a.status == "resolved"),
            "by_category": {c: len(ids) for c, ids in self._category_index.items()},
            "by_severity": {s: len(ids) for s, ids in self._severity_index.items()},
            "critical_active": len(self.get_critical()),
            "recent_5": [a.to_dict() for a in sorted(
                alerts, key=lambda a: a.created_at, reverse=True
            )[:5]],
        }

    def stats(self) -> Dict[str, Any]:
        return {
            "alerts": len(self._alerts),
            "categories": len(self._category_index),
            "history": len(self._alert_history),
        }


def get_alert_center() -> AlertCenter:
    return AlertCenter()
