"""LLMContext — Context management for LLM calls."""
from __future__ import annotations
import time
from typing import Any, Dict, List

class LLMContext:
    __slots__ = ("context_id", "conversation_id", "messages", "system_prompt",
                 "max_context_length", "created_at", "metadata")

    def __init__(self) -> None:
        self.context_id: str = f"ctx_{int(time.time()*1000)}"
        self.conversation_id: str = ""
        self.messages: List[Dict[str, str]] = []
        self.system_prompt: str = ""
        self.max_context_length: int = 128000
        self.created_at: float = time.time()
        self.metadata: Dict[str, Any] = {}

    def add_message(self, role: str, content: str) -> None:
        self.messages.append({"role": role, "content": content})

    def get_messages(self, count: int = 0) -> List[Dict[str, str]]:
        if count > 0:
            return self.messages[-count:]
        return list(self.messages)

    def clear(self) -> int:
        count = len(self.messages)
        self.messages.clear()
        return count

    def to_dict(self) -> Dict[str, Any]:
        return {"context_id": self.context_id, "messages": len(self.messages),
                "system_prompt": bool(self.system_prompt)}
