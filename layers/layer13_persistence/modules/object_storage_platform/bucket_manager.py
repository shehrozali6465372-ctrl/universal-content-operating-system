"""bucket_manager.py — Bucket management."""
from __future__ import annotations
import time
from typing import Dict, List, Optional


class Bucket:
    """Storage bucket."""
    __slots__ = ("name", "region", "created_at", "object_count", "size_bytes")
    _counter = 0

    def __init__(self, name: str, region: str = "us-east-1") -> None:
        Bucket._counter += 1
        self.name = name
        self.region = region
        self.created_at: float = time.time()
        self.object_count: int = 0
        self.size_bytes: int = 0


class BucketManager:
    """Manages storage buckets."""

    def __init__(self) -> None:
        self._buckets: Dict[str, Bucket] = {}

    def create(self, name: str, region: str = "us-east-1") -> Bucket:
        bucket = Bucket(name, region)
        self._buckets[name] = bucket
        return bucket

    def delete(self, name: str) -> bool:
        return self._buckets.pop(name, None) is not None

    def get(self, name: str) -> Optional[Bucket]:
        return self._buckets.get(name)

    def list_all(self) -> List[Bucket]:
        return list(self._buckets.values())

    def count(self) -> int:
        return len(self._buckets)
