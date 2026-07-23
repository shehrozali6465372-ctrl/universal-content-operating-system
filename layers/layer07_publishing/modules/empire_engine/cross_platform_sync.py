"""CrossPlatformSync — Auto-syncs content across platforms (blog→social, YouTube→FB, etc.)."""
from __future__ import annotations
import threading
import time
import uuid
from typing import Any, Dict, List, Optional


class SyncRule:
    __slots__ = ("id", "source_platform", "target_platform", "trigger_type",
                 "delay_seconds", "format_adapt", "active", "priority")

    def __init__(self, source: str, target: str, trigger: str = "on_publish",
                 delay: int = 0, adapt: bool = True) -> None:
        self.id = str(uuid.uuid4())[:12]
        self.source_platform = source
        self.target_platform = target
        self.trigger_type = trigger
        self.delay_seconds = delay
        self.format_adapt = adapt
        self.active = True
        self.priority = 5

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id, "source": self.source_platform,
            "target": self.target_platform, "trigger": self.trigger_type,
            "delay": self.delay_seconds, "adapt": self.format_adapt,
            "active": self.active,
        }


class SyncEvent:
    __slots__ = ("id", "rule_id", "source_post_id", "target_platform",
                 "target_account_id", "status", "created_at", "completed_at")

    def __init__(self, rule_id: str, source_post_id: str, target_platform: str) -> None:
        self.id = str(uuid.uuid4())[:12]
        self.rule_id = rule_id
        self.source_post_id = source_post_id
        self.target_platform = target_platform
        self.target_account_id = ""
        self.status = "pending"
        self.created_at = time.time()
        self.completed_at = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id, "rule": self.rule_id,
            "source": self.source_post_id, "target": self.target_platform,
            "account": self.target_account_id, "status": self.status,
        }


class CrossPlatformSync:
    """Automatically syncs content across platforms based on rules."""
    _instance: Optional["CrossPlatformSync"] = None
    _lock = threading.Lock()

    DEFAULT_RULES = [
        ("blog", "facebook", "on_publish", 300),
        ("blog", "linkedin", "on_publish", 600),
        ("blog", "x", "on_publish", 180),
        ("blog", "pinterest", "on_publish", 900),
        ("youtube", "facebook", "on_publish", 600),
        ("youtube", "x", "on_publish", 300),
        ("youtube", "linkedin", "on_publish", 900),
        ("instagram", "x", "on_publish", 60),
        ("instagram", "facebook", "on_publish", 60),
        ("wordpress", "medium", "on_publish", 1200),
        ("wordpress", "linkedin", "on_publish", 600),
        ("pinterest", "blog", "on_publish", 300),
    ]

    def __new__(cls) -> "CrossPlatformSync":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True
        self._rules: Dict[str, SyncRule] = {}
        self._events: List[SyncEvent] = []
        self._source_index: Dict[str, List[str]] = {}
        self._load_defaults()

    def _load_defaults(self) -> None:
        for source, target, trigger, delay in self.DEFAULT_RULES:
            rule = SyncRule(source, target, trigger, delay)
            self._rules[rule.id] = rule
            self._source_index.setdefault(source, []).append(rule.id)

    def add_rule(self, source: str, target: str, trigger: str = "on_publish",
                 delay: int = 0, adapt: bool = True) -> SyncRule:
        rule = SyncRule(source, target, trigger, delay, adapt)
        self._rules[rule.id] = rule
        self._source_index.setdefault(source, []).append(rule.id)
        return rule

    def get_rules(self, source: str = "") -> List[SyncRule]:
        if source:
            ids = self._source_index.get(source, [])
            return [self._rules[i] for i in ids if i in self._rules]
        return list(self._rules.values())

    def trigger_sync(self, source_platform: str, source_post_id: str,
                     target_account_ids: Dict[str, str] = None) -> List[SyncEvent]:
        rules = self.get_rules(source_platform)
        events = []
        for rule in rules:
            if not rule.active:
                continue
            event = SyncEvent(rule.id, source_post_id, rule.target_platform)
            if target_account_ids:
                event.target_account_id = target_account_ids.get(rule.target_platform, "")
            event.status = "pending"
            self._events.append(event)
            events.append(event)
        return events

    def complete_sync(self, event_id: str) -> bool:
        for event in self._events:
            if event.id == event_id:
                event.status = "completed"
                event.completed_at = time.time()
                return True
        return False

    def get_pending_syncs(self) -> List[SyncEvent]:
        return [e for e in self._events if e.status == "pending"]

    def get_sync_history(self, source_post_id: str = "") -> List[SyncEvent]:
        if source_post_id:
            return [e for e in self._events if e.source_post_id == source_post_id]
        return self._events

    def get_sync_status(self) -> Dict[str, Any]:
        return {
            "total_rules": len(self._rules),
            "active_rules": sum(1 for r in self._rules.values() if r.active),
            "total_events": len(self._events),
            "pending": sum(1 for e in self._events if e.status == "pending"),
            "completed": sum(1 for e in self._events if e.status == "completed"),
            "source_platforms": list(self._source_index.keys()),
            "rules_by_source": {s: len(ids) for s, ids in self._source_index.items()},
        }

    def stats(self) -> Dict[str, Any]:
        return {
            "rules": len(self._rules),
            "events": len(self._events),
            "sources": len(self._source_index),
        }


def get_cross_platform_sync() -> CrossPlatformSync:
    return CrossPlatformSync()
