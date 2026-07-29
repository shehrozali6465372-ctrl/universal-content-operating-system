"""EmergencyRecovery — Handle crashes, interruptions, and failures."""
from __future__ import annotations
import time
import threading
from typing import Any, Callable, Dict, List, Optional

from layers.layer23_website_manager.automation_engine.models.automation_models import (
    AutomationResult, AutomationStatus,
)
from layers.layer23_website_manager.automation_engine.exceptions import RecoveryError


class EmergencyRecovery:
    """Handle emergency recovery scenarios."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._recovery_handlers: Dict[str, Callable] = {}
        self._recovery_log: List[Dict[str, Any]] = []
        self._max_retries: int = 3

    def register_handler(self, scenario: str, handler: Callable) -> None:
        with self._lock:
            self._recovery_handlers[scenario] = handler

    def recover(self, scenario: str,
                context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        entry = {
            "scenario": scenario,
            "attempt": 1,
            "status": "attempting",
            "timestamp": time.time(),
        }
        attempt = 0
        while attempt < self._max_retries:
            attempt += 1
            handler = self._recovery_handlers.get(scenario)
            if handler:
                try:
                    result = handler(context or {})
                    entry["status"] = "recovered"
                    entry["attempt"] = attempt
                    entry["result"] = result
                    with self._lock:
                        self._recovery_log.append(entry)
                    return entry
                except Exception as exc:
                    entry["error"] = str(exc)
                    time.sleep(1 * attempt)
            else:
                entry["status"] = "no_handler"
                entry["error"] = f"No recovery handler for '{scenario}'"
                with self._lock:
                    self._recovery_log.append(entry)
                return entry

        entry["status"] = "failed"
        entry["attempt"] = attempt
        with self._lock:
            self._recovery_log.append(entry)
        return entry

    def recover_crashed_jobs(self, jobs: List[Dict[str, Any]]) -> int:
        count = 0
        for job in jobs:
            result = self.recover("crashed_job", job)
            if result.get("status") == "recovered":
                count += 1
        return count

    def get_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._lock:
            return self._recovery_log[-limit:]

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            recovered = sum(1 for l in self._recovery_log if l["status"] == "recovered")
            failed = sum(1 for l in self._recovery_log if l["status"] == "failed")
            return {
                "total_incidents": len(self._recovery_log),
                "recovered": recovered,
                "failed": failed,
                "success_rate": round((recovered / max(len(self._recovery_log), 1)) * 100, 1),
                "handlers": len(self._recovery_handlers),
            }
