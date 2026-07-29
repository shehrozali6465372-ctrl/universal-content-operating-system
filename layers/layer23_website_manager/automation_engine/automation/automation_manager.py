"""AutomationManager — Control automation lifecycle."""
from __future__ import annotations
import time
import threading
from typing import Any, Dict, Optional

from layers.layer23_website_manager.automation_engine.models.automation_models import (
    AutomationStatus,
)


class AutomationManager:
    """Manage automation start, stop, pause, resume."""

    def __init__(self) -> None:
        self._status: AutomationStatus = AutomationStatus.IDLE
        self._start_time: Optional[float] = None
        self._lock = threading.RLock()
        self._total_executions: int = 0
        self._total_errors: int = 0

    @property
    def status(self) -> AutomationStatus:
        return self._status

    def start(self) -> Dict[str, Any]:
        with self._lock:
            if self._status == AutomationStatus.RUNNING:
                return {"status": "already_running"}
            self._status = AutomationStatus.RUNNING
            self._start_time = time.time()
            return {"status": "started"}

    def stop(self) -> Dict[str, Any]:
        with self._lock:
            self._status = AutomationStatus.STOPPED
            return {"status": "stopped", "uptime": self.uptime}

    def pause(self) -> Dict[str, Any]:
        with self._lock:
            if self._status != AutomationStatus.RUNNING:
                return {"status": "not_running"}
            self._status = AutomationStatus.PAUSED
            return {"status": "paused"}

    def resume(self) -> Dict[str, Any]:
        with self._lock:
            if self._status != AutomationStatus.PAUSED:
                return {"status": "not_paused"}
            self._status = AutomationStatus.RUNNING
            return {"status": "resumed"}

    def restart(self) -> Dict[str, Any]:
        self.stop()
        return self.start()

    @property
    def uptime(self) -> float:
        if self._start_time and self._status == AutomationStatus.RUNNING:
            return time.time() - self._start_time
        return 0.0

    def record_execution(self, success: bool = True) -> None:
        with self._lock:
            self._total_executions += 1
            if not success:
                self._total_errors += 1

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "status": self._status.value,
                "uptime_seconds": round(self.uptime, 1),
                "total_executions": self._total_executions,
                "total_errors": self._total_errors,
                "is_running": self._status == AutomationStatus.RUNNING,
            }
