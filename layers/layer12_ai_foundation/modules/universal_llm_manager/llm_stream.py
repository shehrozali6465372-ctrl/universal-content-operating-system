"""LLMStream — Streaming response support."""
from __future__ import annotations
import time
from typing import Any, Callable, Dict, List, Optional

class LLMStream:
    __slots__ = ("stream_id", "chunks", "is_complete", "on_chunk", "created_at")

    def __init__(self) -> None:
        self.stream_id: str = f"stream_{int(time.time()*1000)}"
        self.chunks: List[str] = []
        self.is_complete: bool = False
        self.on_chunk: Optional[Callable] = None
        self.created_at: float = time.time()

    def add_chunk(self, chunk: str) -> None:
        self.chunks.append(chunk)
        if self.on_chunk:
            self.on_chunk(chunk)

    def complete(self) -> str:
        self.is_complete = True
        return "".join(self.chunks)

    def get_full_content(self) -> str:
        return "".join(self.chunks)

    def to_dict(self) -> Dict[str, Any]:
        return {"stream_id": self.stream_id, "chunks": len(self.chunks),
                "complete": self.is_complete}
