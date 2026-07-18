"""stream_manager.py — Redis Streams implementation."""
from __future__ import annotations
import time
from typing import Any, Dict, List


class StreamEntry:
    """A stream entry."""
    __slots__ = ("entry_id", "data", "timestamp")
    _counter = 0

    def __init__(self, data: Dict[str, str]) -> None:
        StreamEntry._counter += 1
        self.entry_id: int = StreamEntry._counter
        self.data = data
        self.timestamp: float = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {"entry_id": self.entry_id, "data": dict(self.data)}


class StreamManager:
    """Redis Streams implementation."""

    def __init__(self, max_len: int = 10000) -> None:
        self._streams: Dict[str, List[StreamEntry]] = {}
        self._max_len = max_len

    def add(self, stream_name: str, data: Dict[str, str]) -> StreamEntry:
        if stream_name not in self._streams:
            self._streams[stream_name] = []
        entry = StreamEntry(data)
        self._streams[stream_name].append(entry)
        if len(self._streams[stream_name]) > self._max_len:
            self._streams[stream_name] = self._streams[stream_name][-self._max_len:]
        return entry

    def read(self, stream_name: str, count: int = 10) -> List[StreamEntry]:
        return self._streams.get(stream_name, [])[-count:]

    def trim(self, stream_name: str, max_len: int) -> int:
        stream = self._streams.get(stream_name, [])
        before = len(stream)
        self._streams[stream_name] = stream[-max_len:]
        return before - len(self._streams[stream_name])

    def length(self, stream_name: str) -> int:
        return len(self._streams.get(stream_name, []))

    def delete_stream(self, stream_name: str) -> bool:
        return self._streams.pop(stream_name, None) is not None

    def list_streams(self) -> List[str]:
        return list(self._streams.keys())

    def stats(self) -> Dict[str, Any]:
        lengths = {k: len(v) for k, v in self._streams.items()}
        return {"streams": len(self._streams), "lengths": lengths}
