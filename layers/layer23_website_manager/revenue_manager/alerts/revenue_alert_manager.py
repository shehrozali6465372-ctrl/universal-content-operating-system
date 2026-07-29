"""RevenueAlertManager — Notify on revenue spike/drop, commission approved/rejected, merchant issues."""
from __future__ import annotations
import time, threading
from typing import Any, Dict, List, Optional
from layers.layer23_website_manager.revenue_manager.models.revenue_models import RevenueAlert, AlertSeverity


class RevenueAlertManager:
    def __init__(self):
        self._alerts: List[RevenueAlert] = []; self._lock = threading.Lock()

    def create_alert(self, severity: AlertSeverity, title: str, message: str,
                      metric_value: float = 0.0, threshold: float = 0.0) -> RevenueAlert:
        a = RevenueAlert(severity=severity, title=title, message=message, metric_value=metric_value, threshold=threshold)
        with self._lock: self._alerts.append(a); return a

    def get_unread(self) -> List[RevenueAlert]:
        return [a for a in self._alerts if not a.is_read]

    def mark_read(self, alert_id: str) -> bool:
        for a in self._alerts:
            if a.alert_id == alert_id: a.is_read = True; return True
        return False

    def check_revenue_anomaly(self, current: float, previous: float) -> Optional[RevenueAlert]:
        if previous == 0: return None
        change = ((current - previous) / previous) * 100
        if change > 100: return self.create_alert(AlertSeverity.WARNING, f"Revenue Spike: +{change:.0f}%", f"Revenue surged {change:.0f}%", current, previous)
        if change < -50: return self.create_alert(AlertSeverity.CRITICAL, f"Revenue Drop: {change:.0f}%", f"Revenue dropped {change:.0f}%", current, previous)
        return None

    def get_stats(self) -> Dict:
        return {"total_alerts": len(self._alerts), "unread": len(self.get_unread()),
                "critical": sum(1 for a in self._alerts if a.severity == AlertSeverity.CRITICAL)}
