"""
Retry Manager Module
Layer 1: Core System — Module 7

Manages retries with exponential backoff for failed tasks.
"""

import math
import time
from typing import Dict, Any
from datetime import datetime, timezone
from pathlib import Path
import json
import os
import tempfile
from threading import RLock


class RetryManager:
    """Exponential backoff retry management."""

    def __init__(self, base_delay: float = 1.0, max_delay: float = 300.0, persist_path: str = None):
        if not isinstance(base_delay, (int, float)) or not math.isfinite(base_delay) or base_delay < 0:
            raise ValueError("base_delay must be a finite non-negative number")
        if not isinstance(max_delay, (int, float)) or not math.isfinite(max_delay) or max_delay < 0:
            raise ValueError("max_delay must be a finite non-negative number")
        if max_delay < base_delay:
            raise ValueError("max_delay must be greater than or equal to base_delay")
        self._base_delay = float(base_delay)
        self._max_delay = float(max_delay)
        self._retries: Dict[str, Dict] = {}
        self._persist_path = Path(persist_path) if persist_path else None
        self._lock = RLock()
        self._load()

    def record_failure(self, task_id: str) -> Dict[str, Any]:
        """Record a failure for a task. Returns delay info."""
        if not isinstance(task_id, str) or not task_id.strip():
            raise ValueError("task_id must be a non-empty string")
        with self._lock:
            now = time.time()
            if task_id not in self._retries:
                self._retries[task_id] = {"attempts": 0, "last_failure": now}

            previous = dict(self._retries.get(task_id, {}))
            info = self._retries[task_id]
            info["attempts"] += 1
            info["last_failure"] = now

            attempts = info["attempts"]
            delay = self._max_delay if attempts > 1024 else min(
                self._base_delay * (2 ** (attempts - 1)), self._max_delay
            )
            result = {
                "attempt": info["attempts"],
                "delay_seconds": delay,
                "next_retry_at": datetime.fromtimestamp(now + delay, tz=timezone.utc).isoformat(),
            }
            try:
                self._save()
            except Exception:
                if previous:
                    self._retries[task_id] = previous
                else:
                    self._retries.pop(task_id, None)
                raise
            return result

    def record_success(self, task_id: str) -> None:
        """Reset retry count on success."""
        if not isinstance(task_id, str) or not task_id.strip():
            raise ValueError("task_id must be a non-empty string")
        with self._lock:
            previous = self._retries.get(task_id)
            self._retries.pop(task_id, None)
            try:
                self._save()
            except Exception:
                if previous is not None:
                    self._retries[task_id] = previous
                raise

    def should_retry(self, task_id: str, max_retries: int = 3) -> bool:
        """Check if a task should be retried."""
        if not isinstance(task_id, str) or not task_id.strip():
            raise ValueError("task_id must be a non-empty string")
        if not isinstance(max_retries, int) or isinstance(max_retries, bool) or max_retries < 0:
            raise ValueError("max_retries must be a non-negative integer")
        with self._lock:
            info = self._retries.get(task_id)
            if not info:
                return max_retries > 0
            return info["attempts"] < max_retries

    def get_retry_count(self, task_id: str) -> int:
        with self._lock:
            info = self._retries.get(task_id)
            return info["attempts"] if info else 0

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "tasks_with_retries": len(self._retries),
                "total_retry_count": sum(v["attempts"] for v in self._retries.values()),
            }

    def clear(self) -> None:
        with self._lock:
            previous = dict(self._retries)
            self._retries.clear()
            try:
                self._save()
            except Exception:
                self._retries = previous
                raise

    def _load(self) -> None:
        if not self._persist_path or not self._persist_path.exists():
            return
        try:
            data = json.loads(self._persist_path.read_text(encoding="utf-8"))
            if not isinstance(data, dict) or not isinstance(data.get("retries", {}), dict):
                raise ValueError("retry persistence must contain a retries object")
            retries = data.get("retries", {})
            validated: Dict[str, Dict[str, Any]] = {}
            for task_id, info in retries.items():
                if not isinstance(task_id, str) or not isinstance(info, dict):
                    raise ValueError("invalid retry record")
                attempts = info.get("attempts")
                last_failure = info.get("last_failure")
                if (not isinstance(attempts, int) or isinstance(attempts, bool) or attempts < 1
                        or not isinstance(last_failure, (int, float)) or not math.isfinite(last_failure)):
                    raise ValueError(f"invalid retry record for {task_id!r}")
                validated[task_id] = {"attempts": attempts, "last_failure": float(last_failure)}
            with self._lock:
                self._retries = validated
        except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
            raise RuntimeError(f"Retry persistence is unreadable: {self._persist_path}") from exc

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
