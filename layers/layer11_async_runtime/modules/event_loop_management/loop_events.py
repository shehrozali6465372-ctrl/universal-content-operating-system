"""LoopEvents — Loop lifecycle events."""
from __future__ import annotations
import itertools
import time
from typing import Any, Callable, Dict, List

_LEC = itertools.count(1)
class LoopEvent:
    def __init__(self, event_type: str = "") -> None:
        self.event_id = f"le_{next(_LEC)}"
        self.event_type = event_type
        self.data: Dict[str, Any] = {}
        self.timestamp: float = time.time()

class LoopEvents:
    def __init__(self) -> None:
        self._subscribers: Dict[str, List[Callable]] = {}
        self._events: List[LoopEvent] = []
    def publish(self, event_type: str, data: Dict[str, Any] = None) -> LoopEvent:
        event = LoopEvent(event_type)
        if data: event.data = dict(data)
        self._events.append(event)
        for h in self._subscribers.get(event_type, []):
            try: h(event)
            except Exception: pass
        return event
    def subscribe(self, event_type: str, handler: Callable) -> None:
        self._subscribers.setdefault(event_type, []).append(handler)
    def get_events(self, count: int = 20) -> List[LoopEvent]:
        return self._events[-count:]
    def get_stats(self) -> Dict[str, Any]:
        return {"total": len(self._events)}
