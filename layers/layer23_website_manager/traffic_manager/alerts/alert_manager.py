"""AlertManager — Notify on traffic spikes, drops, viral content, dead pages."""
from __future__ import annotations
import time
import threading
from typing import Any, Dict, List, Optional
from layers.layer23_website_manager.traffic_manager.models.traffic_models import Alert, AlertSeverity


class AlertManager:
    """Monitor traffic and generate alerts for anomalies."""

    def __init__(self) -> None:
        self._alerts: List[Alert] = []
        self._lock = threading.Lock()

    def create_alert(self, severity: AlertSeverity, title: str, message: str,
                      source_type: str = "", article_id: str = "",
                      metric_value: float = 0.0, threshold: float = 0.0) -> Alert:
        alert = Alert(severity=severity, title=title, message=message,
                       source_type=source_type, article_id=article_id,
                       metric_value=metric_value, threshold=threshold)
        with self._lock: self._alerts.append(alert)
        return alert

    def get_unread_alerts(self) -> List[Alert]:
        return [a for a in self._alerts if not a.is_read]

    def mark_read(self, alert_id: str) -> bool:
        for a in self._alerts:
            if a.alert_id == alert_id: a.is_read = True; return True
        return False

    def mark_all_read(self) -> int:
        count = 0
        for a in self._alerts:
            if not a.is_read: a.is_read = True; count += 1
        return count

    def check_traffic_anomaly(self, current: float, previous: float,
                                article_id: str = "") -> Optional[Alert]:
        if previous == 0: return None
        change = ((current - previous) / previous) * 100
        if change > 100:
            return self.create_alert(AlertSeverity.WARNING, f"Traffic spike: +{change:.0f}%",
                                       f"Traffic surged for article {article_id}", article_id=article_id,
                                       metric_value=current, threshold=previous)
        if change < -50:
            return self.create_alert(AlertSeverity.CRITICAL, f"Traffic drop: {change:.0f}%",
                                       f"Traffic dropped sharply for article {article_id}", article_id=article_id,
                                       metric_value=current, threshold=previous)
        return None

    def get_stats(self) -> Dict[str, Any]:
        return {"total_alerts": len(self._alerts), "unread": len(self.get_unread_alerts()),
                "critical": sum(1 for a in self._alerts if a.severity == AlertSeverity.CRITICAL)}
