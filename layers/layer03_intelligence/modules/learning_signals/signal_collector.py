"""Signal Collector - Collects raw signals from various sources."""
from __future__ import annotations
import time
from typing import Dict, List


class Signal:
    """A single raw signal."""
    __slots__ = ("source", "signal_type", "value", "timestamp", "metadata", "post_id")
    def __init__(self, source: str = "", signal_type: str = "", value: float = 0.0, post_id: str = ""):
        self.source = source
        self.signal_type = signal_type
        self.value = value
        self.timestamp = time.time()
        self.metadata: Dict = {}
        self.post_id = post_id
    def to_dict(self) -> Dict:
        return {"source": self.source, "type": self.signal_type, "value": round(self.value, 4),
                "post_id": self.post_id, "timestamp": self.timestamp}


class SignalCollector:
    """Collects raw signals from multiple sources."""
    def __init__(self) -> None:
        self._signals: List[Signal] = []
    def collect(self, signal: Signal) -> None:
        self._signals.append(signal)
    def add(self, source: str, signal_type: str, value: float, post_id: str = "") -> Signal:
        s = Signal(source, signal_type, value, post_id)
        self.collect(s)
        return s
    def get_by_type(self, signal_type: str) -> List[Signal]:
        return [s for s in self._signals if s.signal_type == signal_type]
    def get_by_source(self, source: str) -> List[Signal]:
        return [s for s in self._signals if s.source == source]
    def get_by_post(self, post_id: str) -> List[Signal]:
        return [s for s in self._signals if s.post_id == post_id]
    def count(self) -> int:
        return len(self._signals)
    def clear(self) -> None:
        self._signals.clear()
    def to_dict(self) -> Dict:
        return {"count": self.count(), "signals": [s.to_dict() for s in self._signals[-50:]]}
