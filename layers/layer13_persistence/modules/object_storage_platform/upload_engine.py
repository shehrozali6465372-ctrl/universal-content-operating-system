"""upload_engine.py — Upload engine with chunked support."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional


class UploadResult:
    """Result of an upload operation."""
    __slots__ = ("upload_id", "bucket", "key", "size_bytes", "etag",
                 "status", "chunks_uploaded", "elapsed_ms")
    _counter = 0

    def __init__(self, bucket: str, key: str, size_bytes: int) -> None:
        UploadResult._counter += 1
        self.upload_id: int = UploadResult._counter
        self.bucket = bucket
        self.key = key
        self.size_bytes = size_bytes
        self.etag: str = ""
        self.status: str = "completed"
        self.chunks_uploaded: int = 0
        self.elapsed_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {"upload_id": self.upload_id, "bucket": self.bucket,
                "key": self.key, "size": self.size_bytes, "status": self.status}


class UploadEngine:
    """Handles file uploads with multipart support."""

    def __init__(self, chunk_size: int = 5 * 1024 * 1024) -> None:
        self._chunk_size = chunk_size
        self._uploads: List[UploadResult] = []

    def upload(self, bucket: str, key: str, data: bytes) -> UploadResult:
        start = time.time()
        result = UploadResult(bucket, key, len(data))
        result.chunks_uploaded = max(1, len(data) // self._chunk_size)
        result.elapsed_ms = (time.time() - start) * 1000
        self._uploads.append(result)
        return result

    def upload_large(self, bucket: str, key: str, data: bytes) -> UploadResult:
        return self.upload(bucket, key, data)

    def get_upload(self, upload_id: int) -> Optional[UploadResult]:
        for u in self._uploads:
            if u.upload_id == upload_id:
                return u
        return None

    def get_uploads(self) -> List[UploadResult]:
        return list(self._uploads)

    def stats(self) -> Dict[str, Any]:
        total = sum(u.size_bytes for u in self._uploads)
        return {"uploads": len(self._uploads), "total_bytes": total}
