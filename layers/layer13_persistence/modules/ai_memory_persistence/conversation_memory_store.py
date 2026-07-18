"""conversation_memory_store.py — Conversation memory persistence."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from layers.layer13_persistence.modules.ai_memory_persistence.base_memory_store import BaseMemoryStore, MemoryEntry


class ConversationMemoryStore(BaseMemoryStore):
    """Stores conversation histories and context."""

    def __init__(self, max_entries: int = 5000) -> None:
        super().__init__("conversation", max_entries)
        self._conversations: Dict[str, List[Dict[str, str]]] = {}

    def store(self, key: str, value: Any, metadata: Dict[str, Any] = None) -> MemoryEntry:
        entry = MemoryEntry(key, value, "conversation")
        if metadata:
            entry.metadata = metadata
        self._store[key] = entry
        if key not in self._conversations:
            self._conversations[key] = []
        if isinstance(value, dict):
            self._conversations[key].append(value)
        return entry

    def retrieve(self, key: str) -> Optional[MemoryEntry]:
        entry = self._store.get(key)
        if entry:
            entry.access_count += 1
        return entry

    def add_message(self, conversation_id: str, role: str, content: str) -> None:
        if conversation_id not in self._conversations:
            self._conversations[conversation_id] = []
        self._conversations[conversation_id].append({"role": role, "content": content})

    def get_conversation(self, conversation_id: str) -> List[Dict[str, str]]:
        return list(self._conversations.get(conversation_id, []))

    def get_recent_messages(self, conversation_id: str, limit: int = 10) -> List[Dict[str, str]]:
        msgs = self._conversations.get(conversation_id, [])
        return msgs[-limit:]

    def conversation_count(self) -> int:
        return len(self._conversations)

    def stats(self) -> Dict[str, Any]:
        base = super().stats()
        base["conversations"] = self.conversation_count()
        return base
