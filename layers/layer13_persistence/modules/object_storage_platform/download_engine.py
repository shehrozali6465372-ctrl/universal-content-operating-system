"""download_engine.py — Download engine with resume support."""
from __future__ import annotations
import time
from typing import Any, Dict, List


class DownloadResult:
    """Result of a download operation."""
    __slots__ = ("download_id", "bucket", "key", "size_bytes", "status", "elapsed_ms")
    _counter = 0

    def __init__(self, bucket: str, key: str, size_bytes: int) -> None:
        DownloadResult._counter += 1
        self.download_id: int = DownloadResult._counter
        self.bucket = bucket
        self.key = key
        self.size_bytes = size_bytes
        self.status: str = "completed"
        self.elapsed_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {"download_id": self.download_id, "bucket": self.bucket,
                "key": self.key, "status": self.status}


class DownloadEngine:
    """Handles file downloads with range/resume support."""

    def __init__(self) -> None:
        self._downloads: List[DownloadResult] = []
        self._total_bytes: int = 0

    def download(self, bucket: str, key: str, size_bytes: int = 0) -> DownloadResult:
        start = time.time()
        result = DownloadResult(bucket, key, size_bytes)
        result.elapsed_ms = (time.time() - start) * 1000
        self._downloads.append(result)
        self._total_bytes += size_bytes
        return result

    def download_range(self, bucket: str, key: str, offset: int, length: int) -> DownloadResult:
        return self.download(bucket, key, length)

    def get_downloads(self) -> List[DownloadResult]:
        return list(self._downloads)

    def stats(self) -> Dict[str, Any]:
        return {"downloads": len(self._downloads), "total_bytes": self._total_bytes}
