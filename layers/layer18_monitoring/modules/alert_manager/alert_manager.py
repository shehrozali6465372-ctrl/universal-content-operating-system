"""AlertManager — alert rules, evaluation, and notification routing."""
from __future__ import annotations
import time
import uuid
from typing import Any, Callable, Dict, List, Optional
from enum import Enum


class AlertSeverity(str, Enum):
    INFO = "info"; WARNING = "warning"; ERROR = "error"; CRITICAL = "critical"


class AlertState(str, Enum):
    PENDING = "pending"; FIRING = "firing"; RESOLVED = "resolved"; SILENCED = "silenced"


class AlertRule:
    __slots__ = ("rule_id", "name", "condition", "severity", "message",
                 "cooldown_seconds", "last_fired", "active", "metadata")

    def __init__(self, name: str, condition: Callable, severity: AlertSeverity = AlertSeverity.WARNING,
                 message: str = "", cooldown_seconds: float = 300.0) -> None:
        self.rule_id = f"rule_{name}"
        self.name = name
        self.condition = condition
        self.severity = severity
        self.message = message
        self.cooldown_seconds = cooldown_seconds
        self.last_fired: float = 0.0
        self.active = True
        self.metadata: Dict[str, Any] = {}


class Alert:
    __slots__ = ("alert_id", "rule_id", "severity", "state", "message",
                 "created_at", "resolved_at", "metadata")

    def __init__(self, rule_id: str, severity: AlertSeverity, message: str) -> None:
        self.alert_id = str(uuid.uuid4())[:12]
        self.rule_id = rule_id
        self.severity = severity
        self.state = AlertState.FIRING
        self.message = message
        self.created_at = time.time()
        self.resolved_at: float = 0.0
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {"alert_id": self.alert_id, "rule_id": self.rule_id,
                "severity": self.severity.value, "state": self.state.value,
                "message": self.message, "created_at": self.created_at}


class AlertManager:
    def __init__(self) -> None:
        self._rules: Dict[str, AlertRule] = {}
        self._alerts: Dict[str, Alert] = {}
        self._history: List[Dict[str, Any]] = []

    def add_rule(self, name: str, condition: Callable, severity: AlertSeverity = AlertSeverity.WARNING,
                 message: str = "", cooldown_seconds: float = 300.0) -> AlertRule:
        rule = AlertRule(name, condition, severity, message, cooldown_seconds)
        self._rules[rule.rule_id] = rule
        return rule

    def evaluate(self, context: Optional[Dict[str, Any]] = None) -> List[Alert]:
        fired = []
        for rule in self._rules.values():
            if not rule.active:
                continue
            if time.time() - rule.last_fired < rule.cooldown_seconds:
                continue
            try:
                if rule.condition(context or {}):
                    alert = Alert(rule.rule_id, rule.severity, rule.message or f"Rule {rule.name} fired")
                    self._alerts[alert.alert_id] = alert
                    rule.last_fired = time.time()
                    fired.append(alert)
                    self._history.append(alert.to_dict())
            except Exception:
                pass
        return fired

    def resolve_alert(self, alert_id: str) -> bool:
        alert = self._alerts.get(alert_id)
        if alert and alert.state == AlertState.FIRING:
            alert.state = AlertState.RESOLVED
            alert.resolved_at = time.time()
            return True
        return False

    def list_alerts(self, state: Optional[AlertState] = None) -> List[Dict[str, Any]]:
        alerts = self._alerts.values()
        if state:
            alerts = [a for a in alerts if a.state == state]
        return [a.to_dict() for a in alerts]

    def list_rules(self) -> List[Dict[str, Any]]:
        return [{"rule_id": r.rule_id, "name": r.name, "severity": r.severity.value,
                 "active": r.active} for r in self._rules.values()]

    def stats(self) -> Dict[str, Any]:
        firing = sum(1 for a in self._alerts.values() if a.state == AlertState.FIRING)
        resolved = sum(1 for a in self._alerts.values() if a.state == AlertState.RESOLVED)
        return {"rules": len(self._rules), "total_alerts": len(self._alerts),
                "firing": firing, "resolved": resolved}
