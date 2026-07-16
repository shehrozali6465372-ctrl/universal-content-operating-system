"""Publisher Metrics — Track publishing performance and health."""
from __future__ import annotations
from typing import Any, Dict, List


class PublisherMetrics:
    """Collect and report publishing metrics."""

    def __init__(self) -> None:
        self._publish_count = 0
        self._success_count = 0
        self._failure_count = 0
        self._total_duration_ms = 0.0
        self._upload_bytes = 0
        self._upload_count = 0
        self._api_latency_ms = 0.0
        self._api_call_count = 0
        self._snapshots: List[Dict[str, Any]] = []

    def record_publish(self, success: bool, duration_ms: float) -> None:
        self._publish_count += 1
        self._total_duration_ms += duration_ms
        if success:
            self._success_count += 1
        else:
            self._failure_count += 1

    def record_upload(self, bytes_uploaded: int) -> None:
        self._upload_count += 1
        self._upload_bytes += bytes_uploaded

    def record_api_call(self, latency_ms: float) -> None:
        self._api_call_count += 1
        self._api_latency_ms += latency_ms

    def take_snapshot(self) -> Dict[str, Any]:
        snap = self.get_current()
        self._snapshots.append(snap)
        return snap

    def get_current(self) -> Dict[str, Any]:
        avg_publish = (
            self._total_duration_ms / max(1, self._publish_count)
        )
        avg_api = (
            self._api_latency_ms / max(1, self._api_call_count)
        )
        success_rate = (
            self._success_count / max(1, self._publish_count)
        )
        return {
            "publish_count": self._publish_count,
            "success_count": self._success_count,
            "failure_count": self._failure_count,
            "success_rate": round(success_rate, 3),
            "avg_publish_duration_ms": round(avg_publish, 2),
            "upload_count": self._upload_count,
            "upload_bytes": self._upload_bytes,
            "api_call_count": self._api_call_count,
            "avg_api_latency_ms": round(avg_api, 2),
        }

    def get_snapshots(self) -> List[Dict[str, Any]]:
        return list(self._snapshots)

    def reset(self) -> None:
        self._publish_count = 0
        self._success_count = 0
        self._failure_count = 0
        self._total_duration_ms = 0.0
        self._upload_bytes = 0
        self._upload_count = 0
        self._api_latency_ms = 0.0
        self._api_call_count = 0
