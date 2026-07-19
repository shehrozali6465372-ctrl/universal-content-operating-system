"""EventBusIntegration — unified event bus connecting all layers."""
from __future__ import annotations
import time
from typing import Any, Callable, Dict, List, Optional

class EventBusIntegration:
    def __init__(self) -> None:
        self._global_subscribers: Dict[str, List[Callable]] = {}
        self._global_log: List[Dict[str, Any]] = []
        self._layer_buses: Dict[str, Any] = {}

    def register_layer_bus(self, layer: str, bus: Any) -> None:
        self._layer_buses[layer] = bus

    def publish_global(self, event_type: str, data: Optional[Dict[str, Any]] = None,
                       source_layer: str = '') -> None:
        entry = {'event': event_type, 'data': data or {}, 'source': source_layer,
                 'timestamp': time.time()}
        self._global_log.append(entry)
        for cb in self._global_subscribers.get(event_type, []):
            try: cb(data or {})
            except Exception: pass
        # Also publish to registered layer buses
        for layer, bus in self._layer_buses.items():
            if hasattr(bus, 'publish'):
                try: bus.publish(event_type, data)
                except Exception: pass

    def subscribe_global(self, event_type: str, callback: Callable) -> None:
        self._global_subscribers.setdefault(event_type, []).append(callback)

    def get_log(self, event_type: Optional[str] = None,
                source_layer: Optional[str] = None) -> List[Dict[str, Any]]:
        results = self._global_log
        if event_type: results = [e for e in results if e['event'] == event_type]
        if source_layer: results = [e for e in results if e['source'] == source_layer]
        return results

    def count(self) -> int:
        return len(self._global_log)

    def clear(self) -> None:
        self._global_log.clear()
