"""chunk_uploader.py — Chunked upload management."""
from __future__ import annotations
import time
from typing import Dict, List


class ChunkInfo:
    """Information about an uploaded chunk."""
    __slots__ = ("chunk_number", "size_bytes", "etag", "uploaded_at")

    def __init__(self, chunk_number: int, size_bytes: int) -> None:
        self.chunk_number = chunk_number
        self.size_bytes = size_bytes
        self.etag: str = ""
        self.uploaded_at: float = time.time()


class ChunkUploader:
    """Manages chunked file uploads."""

    def __init__(self, chunk_size: int = 5 * 1024 * 1024) -> None:
        self._chunk_size = chunk_size
        self._uploads: Dict[str, List[ChunkInfo]] = {}

    def start_upload(self, upload_id: str) -> None:
        self._uploads[upload_id] = []

    def add_chunk(self, upload_id: str, chunk_number: int, size_bytes: int) -> ChunkInfo:
        if upload_id not in self._uploads:
            self._uploads[upload_id] = []
        chunk = ChunkInfo(chunk_number, size_bytes)
        self._uploads[upload_id].append(chunk)
        return chunk

    def get_chunks(self, upload_id: str) -> List[ChunkInfo]:
        return self._uploads.get(upload_id, [])

    def is_complete(self, upload_id: str, expected_chunks: int) -> bool:
        return len(self._uploads.get(upload_id, [])) >= expected_chunks

    def calculate_chunks(self, total_size: int) -> int:
        return max(1, (total_size + self._chunk_size - 1) // self._chunk_size)

    def delete_upload(self, upload_id: str) -> bool:
        return self._uploads.pop(upload_id, None) is not None
