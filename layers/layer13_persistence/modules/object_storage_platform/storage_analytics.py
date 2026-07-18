"""storage_analytics.py — Storage analytics."""
from __future__ import annotations
import time
from typing import Any, Dict, List


class StorageAnalytics:
    """Tracks storage analytics."""

    def __init__(self) -> None:
        self._operations: List[Dict[str, Any]] = []
        self._by_bucket: Dict[str, Dict[str, int]] = {}

    def record_operation(self, op_type: str, bucket: str, size_bytes: int) -> None:
        self._operations.append({"type": op_type, "bucket": bucket,
                                  "size": size_bytes, "time": time.time()})
        if bucket not in self._by_bucket:
            self._by_bucket[bucket] = {"uploads": 0, "downloads": 0, "bytes": 0}
        if op_type == "upload":
            self._by_bucket[bucket]["uploads"] += 1
        elif op_type == "download":
            self._by_bucket[bucket]["downloads"] += 1
        self._by_bucket[bucket]["bytes"] += size_bytes

    def get_bucket_stats(self, bucket: str) -> Dict[str, int]:
        return self._by_bucket.get(bucket, {"uploads": 0, "downloads": 0, "bytes": 0})

    def get_total_operations(self) -> int:
        return len(self._operations)

    def get_total_bytes(self) -> int:
        return sum(self._by_bucket[b]["bytes"] for b in self._by_bucket)

    def to_dict(self) -> Dict[str, Any]:
        return {"total_operations": self._operations.__len__(),
                "by_bucket": dict(self._by_bucket)}
