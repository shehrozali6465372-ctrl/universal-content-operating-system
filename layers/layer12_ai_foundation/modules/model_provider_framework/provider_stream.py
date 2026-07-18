"""provider_stream.py — Streaming response support."""
from __future__ import annotations
from typing import Any, Callable, Dict, Generator, List


class StreamChunk:
    """Single chunk from a streaming response."""
    __slots__ = ("content", "delta", "finish_reason", "metadata")

    def __init__(self, content: str = "", delta: str = "") -> None:
        self.content = content
        self.delta = delta
        self.finish_reason: str = ""
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {"content": self.content, "delta": self.delta,
                "finish_reason": self.finish_reason}


class ProviderStream:
    """Manages streaming responses from providers."""

    def __init__(self) -> None:
        self._callbacks: List[Callable] = []

    def on_chunk(self, callback: Callable) -> None:
        self._callbacks.append(callback)

    def create_stream(self, chunks: List[str]) -> Generator[StreamChunk, None, None]:
        accumulated = ""
        for chunk_text in chunks:
            accumulated += chunk_text
            chunk = StreamChunk(content=accumulated, delta=chunk_text)
            for cb in self._callbacks:
                cb(chunk)
            yield chunk
        final = StreamChunk(content=accumulated)
        final.finish_reason = "stop"
        for cb in self._callbacks:
            cb(final)
        yield final

    def get_full_content(self, chunks: List[str]) -> str:
        return "".join(chunks)
