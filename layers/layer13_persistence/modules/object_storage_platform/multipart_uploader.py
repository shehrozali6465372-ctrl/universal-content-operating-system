"""multipart_uploader.py — Multipart upload management."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional


class MultipartUpload:
    """A multipart upload session."""
    __slots__ = ("upload_id", "bucket", "key", "parts", "status", "created_at")
    _counter = 0

    def __init__(self, bucket: str, key: str) -> None:
        MultipartUpload._counter += 1
        self.upload_id: int = MultipartUpload._counter
        self.bucket = bucket
        self.key = key
        self.parts: List[Dict[str, Any]] = []
        self.status: str = "in_progress"
        self.created_at: float = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {"upload_id": self.upload_id, "bucket": self.bucket,
                "key": self.key, "status": self.status, "parts": len(self.parts)}


class MultipartUploader:
    """Manages multipart uploads."""

    def __init__(self) -> None:
        self._uploads: Dict[int, MultipartUpload] = {}

    def initiate(self, bucket: str, key: str) -> MultipartUpload:
        upload = MultipartUpload(bucket, key)
        self._uploads[upload.upload_id] = upload
        return upload

    def add_part(self, upload_id: int, part_number: int, etag: str = "") -> bool:
        upload = self._uploads.get(upload_id)
        if upload:
            upload.parts.append({"part_number": part_number, "etag": etag})
            return True
        return False

    def complete(self, upload_id: int) -> bool:
        upload = self._uploads.get(upload_id)
        if upload:
            upload.status = "completed"
            return True
        return False

    def abort(self, upload_id: int) -> bool:
        upload = self._uploads.get(upload_id)
        if upload:
            upload.status = "aborted"
            return True
        return False

    def get_upload(self, upload_id: int) -> Optional[MultipartUpload]:
        return self._uploads.get(upload_id)

    def list_uploads(self) -> List[MultipartUpload]:
        return list(self._uploads.values())
