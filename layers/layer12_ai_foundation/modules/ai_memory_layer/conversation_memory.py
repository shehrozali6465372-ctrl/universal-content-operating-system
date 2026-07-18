"""ConversationMemory — store and manage conversation history."""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from .models import MemoryEntry, MemoryType


class ConversationMemory:
    """Store and manage conversation history between user and AI."""

    def __init__(self, max_turns: int = 100) -> None:
        self.max_turns = max_turns
        self._conversations: Dict[str, List[Dict[str, Any]]] = {}
        self._entries: List[MemoryEntry] = []

    def add_turn(self, session_id: str, role: str, content: str,
                 metadata: Optional[Dict[str, Any]] = None) -> None:
        turn = {"role": role, "content": content, "timestamp": time.time(),
                "metadata": metadata or {}}
        if session_id not in self._conversations:
            self._conversations[session_id] = []
        self._conversations[session_id].append(turn)
        if len(self._conversations[session_id]) > self.max_turns:
            self._conversations[session_id] = self._conversations[session_id][-self.max_turns:]

        entry = MemoryEntry(
            content=f"[{role}] {content}", memory_type=MemoryType.CONVERSATIONAL,
            metadata={"session_id": session_id, "role": role},
        )
        self._entries.append(entry)

    def get_history(self, session_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        return self._conversations.get(session_id, [])[-limit:]

    def get_last_user_message(self, session_id: str) -> str:
        history = self._conversations.get(session_id, [])
        for turn in reversed(history):
            if turn["role"] == "user":
                return turn["content"]
        return ""

    def get_summary(self, session_id: str) -> Dict[str, Any]:
        history = self._conversations.get(session_id, [])
        user_turns = sum(1 for t in history if t["role"] == "user")
        ai_turns = sum(1 for t in history if t["role"] == "assistant")
        return {"session_id": session_id, "total_turns": len(history),
                "user_turns": user_turns, "ai_turns": ai_turns}

    def search(self, query: str, limit: int = 5) -> List[MemoryEntry]:
        query_words = set(query.lower().split())
        scored = []
        for e in self._entries:
            content_words = set(e.content.lower().split())
            overlap = query_words & content_words
            score = len(overlap) / max(len(query_words), 1) if query_words else 0.0
            if score > 0:
                scored.append((e, score))
        scored.sort(key=lambda x: x[1], reverse=True)
        return [e for e, _ in scored[:limit]]

    def clear_session(self, session_id: str) -> None:
        self._conversations.pop(session_id, None)

    def count(self) -> int:
        return len(self._entries)
