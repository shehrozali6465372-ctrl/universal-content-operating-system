"""
Retry Manager Module
Layer 1: Core System — Module 7

Manages retries with exponential backoff for failed tasks.
"""

import time
from typing import Dict, Any
from datetime import datetime, timezone
from pathlib import Path
import json
import os
import tempfile


class RetryManager:
    """Exponential backoff retry management."""

    def __init__(self, base_delay: float = 1.0, max_delay: float = 300.0, persist_path: str = None):
        self._base_delay = base_delay
        self._max_delay = max_delay
        self._retries: Dict[str, Dict] = {}
        self._persist_path = Path(persist_path) if persist_path else None
        self._load()

    def record_failure(self, task_id: str) -> Dict[str, Any]:
        """Record a failure for a task. Returns delay info."""
        now = time.time()
        if task_id not in self._retries:
            self._retries[task_id] = {"attempts": 0, "last_failure": now}

        info = self._retries[task_id]
        info["attempts"] += 1
        info["last_failure"] = now

        delay = min(self._base_delay * (2 ** (info["attempts"] - 1)), self._max_delay)
        result = {
            "attempt": info["attempts"],
            "delay_seconds": delay,
            "next_retry_at": datetime.fromtimestamp(now + delay, tz=timezone.utc).isoformat(),
        }
        self._save()
        return result

    def record_success(self, task_id: str) -> None:
        """Reset retry count on success."""
        self._retries.pop(task_id, None)
        self._save()

    def should_retry(self, task_id: str, max_retries: int = 3) -> bool:
        """Check if a task should be retried."""
        info = self._retries.get(task_id)
        if not info:
            return True
        return info["attempts"] < max_retries

    def get_retry_count(self, task_id: str) -> int:
        info = self._retries.get(task_id)
        return info["attempts"] if info else 0

    def get_stats(self) -> Dict[str, Any]:
        return {
            "tasks_with_retries": len(self._retries),
            "total_retry_count": sum(v["attempts"] for v in self._retries.values()),
        }

    def clear(self) -> None:
        self._retries.clear()
        self._save()

    def _load(self) -> None:
        if not self._persist_path or not self._persist_path.exists():
            return
        data = json.loads(self._persist_path.read_text(encoding="utf-8"))
        self._retries = data.get("retries", {})

    def _save(self) -> None:
        if not self._persist_path:
            return
        self._persist_path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_name = tempfile.mkstemp(dir=str(self._persist_path.parent), prefix=".retry.", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump({"retries": self._retries}, f, indent=2)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_name, self._persist_path)
        except Exception:
            try:
                os.unlink(tmp_name)
            except OSError:
                pass
            raise
