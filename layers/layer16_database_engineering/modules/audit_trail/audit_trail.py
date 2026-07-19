"""AuditTrail — track all data modifications for compliance."""
from __future__ import annotations
import time
import uuid
from typing import Any, Dict, List, Optional
from enum import Enum


class AuditAction(str, Enum):
    CREATE = "create"; READ = "read"; UPDATE = "update"; DELETE = "delete"


class AuditEntry:
    __slots__ = ("entry_id", "action", "table_name", "entity_id",
                 "old_data", "new_data", "user_id", "timestamp", "metadata")

    def __init__(self, action: AuditAction, table_name: str, entity_id: str,
                 user_id: str = "system") -> None:
        self.entry_id = str(uuid.uuid4())[:12]
        self.action = action
        self.table_name = table_name
        self.entity_id = entity_id
        self.old_data: Optional[Dict[str, Any]] = None
        self.new_data: Optional[Dict[str, Any]] = None
        self.user_id = user_id
        self.timestamp = time.time()
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {"entry_id": self.entry_id, "action": self.action.value,
                "table_name": self.table_name, "entity_id": self.entity_id,
                "user_id": self.user_id, "timestamp": self.timestamp}


class AuditTrail:
    def __init__(self, max_entries: int = 10000) -> None:
        self._entries: List[AuditEntry] = []
        self._max_entries = max_entries

    def log(self, action: AuditAction, table_name: str, entity_id: str,
            old_data: Optional[Dict[str, Any]] = None,
            new_data: Optional[Dict[str, Any]] = None,
            user_id: str = "system") -> AuditEntry:
        entry = AuditEntry(action, table_name, entity_id, user_id)
        entry.old_data = old_data
        entry.new_data = new_data
        self._entries.append(entry)
        if len(self._entries) > self._max_entries:
            self._entries = self._entries[-self._max_entries:]
        return entry

    def query(self, table_name: Optional[str] = None,
              action: Optional[AuditAction] = None,
              entity_id: Optional[str] = None,
              limit: int = 100) -> List[Dict[str, Any]]:
        results = self._entries
        if table_name:
            results = [e for e in results if e.table_name == table_name]
        if action:
            results = [e for e in results if e.action == action]
        if entity_id:
            results = [e for e in results if e.entity_id == entity_id]
        return [e.to_dict() for e in results[-limit:]]

    def count(self) -> int:
        return len(self._entries)

    def clear(self) -> int:
        count = len(self._entries)
        self._entries.clear()
        return count
