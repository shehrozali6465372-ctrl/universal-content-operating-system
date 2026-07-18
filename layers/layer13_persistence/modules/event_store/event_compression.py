"""event_compression.py — Event compression."""
from __future__ import annotations
import json
from typing import Any, Dict, List
from layers.layer13_persistence.modules.event_store.event import Event


class EventCompressor:
    """Compresses events for storage efficiency."""

    def __init__(self) -> None:
        self._compressed_count: int = 0

    def compress_events(self, events: List[Event]) -> bytes:
        data = [{"type": e.event_type, "agg": e.aggregate_id,
                  "data": e.data, "ts": e.timestamp} for e in events]
        compressed = json.dumps(data).encode()
        self._compressed_count += len(events)
        return compressed

    def get_compression_ratio(self, original: bytes, compressed: bytes) -> float:
        if len(original) == 0:
            return 0.0
        return len(compressed) / len(original)

    def stats(self) -> Dict[str, Any]:
        return {"compressed_events": self._compressed_count}
