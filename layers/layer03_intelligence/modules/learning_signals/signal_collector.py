"""Bounded thread-safe collector for raw learning signals."""
from __future__ import annotations
import copy
import time
from threading import RLock
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
        return {
            "source": self.source,
            "type": self.signal_type,
            "value": round(self.value, 4),
            "post_id": self.post_id,
            "timestamp": self.timestamp,
        }


class SignalCollector:
    """Collects raw signals with a bounded in-memory retention policy."""

    def __init__(self, max_signals: int = 5000) -> None:
        if max_signals < 1:
            raise ValueError("max_signals must be >= 1")
        self._signals: List[Signal] = []
        self._max_signals = max_signals
        self._lock = RLock()

    @staticmethod
    def _snapshot(signal: Signal) -> Signal:
        return copy.deepcopy(signal)

    def collect(self, signal: Signal) -> None:
        with self._lock:
            if len(self._signals) >= self._max_signals:
                self._signals.pop(0)
            self._signals.append(self._snapshot(signal))

    def add(self, source: str, signal_type: str, value: float, post_id: str = "") -> Signal:
        signal = Signal(source, signal_type, value, post_id)
        self.collect(signal)
        return signal

    def get_by_type(self, signal_type: str) -> List[Signal]:
        with self._lock:
            return [self._snapshot(s) for s in self._signals if s.signal_type == signal_type]

    def get_by_source(self, source: str) -> List[Signal]:
        with self._lock:
            return [self._snapshot(s) for s in self._signals if s.source == source]

    def get_by_post(self, post_id: str) -> List[Signal]:
        with self._lock:
            return [self._snapshot(s) for s in self._signals if s.post_id == post_id]

    def count(self) -> int:
        with self._lock:
            return len(self._signals)

    def clear(self) -> None:
        with self._lock:
            self._signals.clear()

    def to_dict(self) -> Dict:
        with self._lock:
            return {
                "count": len(self._signals),
                "signals": [s.to_dict() for s in self._signals[-50:]],
            }
