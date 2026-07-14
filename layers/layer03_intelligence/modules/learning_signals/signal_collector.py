"""Signal Collector — normalizes feedback into learning signals."""
from typing import Dict, List
from datetime import datetime, timezone

class Signal:
    __slots__ = ("signal_id", "signal_type", "source", "value", "confidence", "metadata", "timestamp")
    def __init__(self, signal_type: str, source: str = "", value: float = 0.0, confidence: float = 0.8):
        self.signal_id = f"sig_{hash(signal_type) % 1000000}"
        self.signal_type = signal_type
        self.source = source
        self.value = value
        self.confidence = confidence
        self.metadata: Dict = {}
        self.timestamp = datetime.now(timezone.utc).isoformat()
    def to_dict(self) -> dict:
        return {"signal_id": self.signal_id, "signal_type": self.signal_type,
                "source": self.source, "value": self.value, "confidence": self.confidence,
                "timestamp": self.timestamp}

class SignalCollector:
    def __init__(self):
        self._signals: List[Signal] = []
    def collect(self, signal: Signal):
        self._signals.append(signal)
    def get_by_type(self, signal_type: str) -> List[Signal]:
        return [s for s in self._signals if s.signal_type == signal_type]
    def get_recent(self, n: int = 10) -> List[Signal]:
        return self._signals[-n:]
    def compute_average(self, signal_type: str) -> float:
        sigs = self.get_by_type(signal_type)
        if not sigs: return 0.0
        return round(sum(s.value for s in sigs) / len(sigs), 3)
    def compute_success_rate(self) -> float:
        if not self._signals: return 0.0
        success = sum(1 for s in self._signals if s.signal_type == "success")
        return round(success / len(self._signals), 3)
    def count(self) -> int:
        return len(self._signals)
    def clear(self):
        self._signals.clear()
