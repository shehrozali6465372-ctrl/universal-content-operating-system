"""NotificationManager — Send and manage workflow notifications."""
from __future__ import annotations
import time
import threading
from typing import Any, Callable, Dict, List, Optional

from layers.layer23_website_manager.scheduler_orchestrator.models.scheduler_models import Notification


class NotificationManager:
    """Manage notifications for workflow events."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._notifications: List[Notification] = []
        self._channels: List[Callable] = []

    def register_channel(self, channel: Callable) -> None:
        with self._lock:
            self._channels.append(channel)

    def send(self, title: str, message: str, level: str = "info",
             source: str = "", job_id: str = "") -> Notification:
        notif = Notification(title=title, message=message, level=level,
                             source=source, job_id=job_id)
        with self._lock:
            self._notifications.append(notif)
            channels = list(self._channels)
        for channel in channels:
            try:
                channel(notif)
            except Exception:
                pass
        return notif

    def get_unread(self) -> List[Notification]:
        with self._lock:
            return [n for n in self._notifications if not n.read]

    def mark_read(self, notification_id: str) -> bool:
        with self._lock:
            for n in self._notifications:
                if n.notification_id == notification_id:
                    n.read = True
                    return True
            return False

    def mark_all_read(self) -> int:
        with self._lock:
            count = sum(1 for n in self._notifications if not n.read)
            for n in self._notifications:
                n.read = True
            return count

    def get_all(self, limit: int = 100) -> List[Dict[str, Any]]:
        with self._lock:
            return [n.to_dict() for n in self._notifications[-limit:]]

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "total": len(self._notifications),
                "unread": len(self.get_unread()),
                "channels": len(self._channels),
                "by_level": {
                    level: sum(1 for n in self._notifications if n.level == level)
                    for level in {"info", "warning", "error", "critical"}
                },
            }
