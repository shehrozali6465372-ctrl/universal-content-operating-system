"""Thread-safe alert rules, lifecycle and bounded history."""
from __future__ import annotations

import threading
import time
import uuid
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertState(str, Enum):
    PENDING = "pending"
    FIRING = "firing"
    RESOLVED = "resolved"
    SILENCED = "silenced"


class AlertRule:
    __slots__ = ("rule_id", "name", "condition", "severity", "message", "cooldown_seconds",
                 "last_fired", "active", "metadata")

    def __init__(self, name: str, condition: Callable[[Dict[str, Any]], bool],
                 severity: AlertSeverity = AlertSeverity.WARNING, message: str = "",
                 cooldown_seconds: float = 300.0) -> None:
        if not name.strip():
            raise ValueError("rule name is required")
        if cooldown_seconds < 0:
            raise ValueError("cooldown_seconds cannot be negative")
        self.rule_id = f"rule_{name}_{uuid.uuid4().hex[:8]}"
        self.name, self.condition, self.severity = name, condition, severity
        self.message, self.cooldown_seconds = message, cooldown_seconds
        self.last_fired = 0.0
        self.active = True
        self.metadata: Dict[str, Any] = {}


class Alert:
    __slots__ = ("alert_id", "rule_id", "severity", "state", "message",
                 "created_at", "resolved_at", "metadata")

    def __init__(self, rule_id: str, severity: AlertSeverity, message: str) -> None:
        self.alert_id = str(uuid.uuid4())
        self.rule_id, self.severity, self.state = rule_id, severity, AlertState.FIRING
        self.message, self.created_at = message, time.time()
        self.resolved_at = 0.0
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {"alert_id": self.alert_id, "rule_id": self.rule_id,
                "severity": self.severity.value, "state": self.state.value,
                "message": self.message, "created_at": self.created_at,
                "resolved_at": self.resolved_at}


class AlertManager:
    def __init__(self, history_size: int = 1000) -> None:
        if history_size <= 0:
            raise ValueError("history_size must be positive")
        self._lock = threading.RLock()
        self._history_size = history_size
        self._rules: Dict[str, AlertRule] = {}
        self._alerts: Dict[str, Alert] = {}
        self._history: List[Dict[str, Any]] = []
        self._condition_errors = 0

    def add_rule(self, name: str, condition: Callable[[Dict[str, Any]], bool],
                 severity: AlertSeverity = AlertSeverity.WARNING, message: str = "",
                 cooldown_seconds: float = 300.0) -> AlertRule:
        rule = AlertRule(name, condition, severity, message, cooldown_seconds)
        with self._lock:
            self._rules[rule.rule_id] = rule
        return rule

    def evaluate(self, context: Optional[Dict[str, Any]] = None) -> List[Alert]:
        now = time.time()
        fired: List[Alert] = []
        safe_context = dict(context or {})
        with self._lock:
            rules = list(self._rules.values())
            for rule in rules:
                if not rule.active or now - rule.last_fired < rule.cooldown_seconds:
                    continue
                try:
                    matched = bool(rule.condition(safe_context))
                except Exception:
                    self._condition_errors += 1
                    continue
                if matched:
                    alert = Alert(rule.rule_id, rule.severity,
                                  rule.message or f"Rule {rule.name} fired")
                    self._alerts[alert.alert_id] = alert
                    rule.last_fired = now
                    fired.append(alert)
                    self._history.append(alert.to_dict())
                    if len(self._history) > self._history_size:
                        del self._history[:-self._history_size]
        return fired

    def resolve_alert(self, alert_id: str) -> bool:
        with self._lock:
            alert = self._alerts.get(alert_id)
            if not alert or alert.state != AlertState.FIRING:
                return False
            alert.state = AlertState.RESOLVED
            alert.resolved_at = time.time()
            return True

    def list_alerts(self, state: Optional[AlertState] = None) -> List[Dict[str, Any]]:
        with self._lock:
            alerts = list(self._alerts.values())
            if state is not None:
                alerts = [a for a in alerts if a.state == state]
            return [a.to_dict() for a in alerts]

    def list_rules(self) -> List[Dict[str, Any]]:
        with self._lock:
            return [{"rule_id": r.rule_id, "name": r.name, "severity": r.severity.value,
                     "active": r.active} for r in self._rules.values()]

    def stats(self) -> Dict[str, Any]:
        with self._lock:
            firing = sum(a.state == AlertState.FIRING for a in self._alerts.values())
            resolved = sum(a.state == AlertState.RESOLVED for a in self._alerts.values())
            return {"rules": len(self._rules), "total_alerts": len(self._alerts),
                    "firing": firing, "resolved": resolved,
                    "condition_errors": self._condition_errors}
