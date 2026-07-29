"""TriggerEngine — Evaluate and fire automation triggers."""
from __future__ import annotations
import time
import threading
from typing import Any, Callable, Dict, List, Optional

from layers.layer23_website_manager.automation_engine.models.automation_models import (
    Trigger, TriggerType,
)
from layers.layer23_website_manager.automation_engine.exceptions import TriggerError


class TriggerEngine:
    """Manage and evaluate automation triggers."""

    def __init__(self) -> None:
        self._triggers: Dict[str, Trigger] = {}
        self._handlers: Dict[TriggerType, List[Callable]] = {}
        self._lock = threading.RLock()

    def register_trigger(self, name: str, trigger_type: TriggerType,
                         config: Optional[Dict[str, Any]] = None,
                         cooldown: float = 300.0) -> Trigger:
        trigger = Trigger(name, trigger_type, config, cooldown)
        with self._lock:
            self._triggers[trigger.trigger_id] = trigger
        return trigger

    def unregister_trigger(self, trigger_id: str) -> bool:
        with self._lock:
            return self._triggers.pop(trigger_id, None) is not None

    def get_trigger(self, trigger_id: str) -> Optional[Trigger]:
        return self._triggers.get(trigger_id)

    def get_all_triggers(self) -> List[Trigger]:
        return list(self._triggers.values())

    def enable_trigger(self, trigger_id: str) -> bool:
        t = self._triggers.get(trigger_id)
        if not t:
            return False
        t.enabled = True
        return True

    def disable_trigger(self, trigger_id: str) -> bool:
        t = self._triggers.get(trigger_id)
        if not t:
            return False
        t.enabled = False
        return True

    def register_handler(self, trigger_type: TriggerType, handler: Callable) -> None:
        with self._lock:
            if trigger_type not in self._handlers:
                self._handlers[trigger_type] = []
            self._handlers[trigger_type].append(handler)

    def evaluate(self, trigger_id: str,
                 context: Optional[Dict[str, Any]] = None) -> bool:
        trigger = self._triggers.get(trigger_id)
        if not trigger or not trigger.can_fire:
            return False
        trigger.fire()
        with self._lock:
            handlers = list(self._handlers.get(trigger.trigger_type, []))
        for handler in handlers:
            try:
                handler(trigger, context or {})
            except Exception:
                pass
        return True

    def evaluate_all(self, context: Optional[Dict[str, Any]] = None) -> List[str]:
        fired = []
        for trigger in self._triggers.values():
            if self.evaluate(trigger.trigger_id, context):
                fired.append(trigger.trigger_id)
        return fired

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "total_triggers": len(self._triggers),
                "enabled": sum(1 for t in self._triggers.values() if t.enabled),
                "total_fires": sum(t.fire_count for t in self._triggers.values()),
                "handlers": sum(len(h) for h in self._handlers.values()),
            }
