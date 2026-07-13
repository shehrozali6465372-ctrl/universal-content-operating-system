"""
Backup Entry
Layer 1: Core System — Module 10

Metadata model for each backup.
"""

from datetime import datetime, timezone
from typing import Optional


class BackupEntry:
    """Metadata for a single backup."""

    __slots__ = (
        "backup_id", "source", "filepath", "size_bytes",
        "hash_sha256", "encrypted", "compressed",
        "created_at", "retention_days", "description",
    )

    def __init__(
        self,
        backup_id: str,
        source: str,
        filepath: str,
        size_bytes: int = 0,
        hash_sha256: str = "",
        encrypted: bool = False,
        compressed: bool = False,
        retention_days: int = 30,
        description: str = "",
    ):
        self.backup_id = backup_id
        self.source = source
        self.filepath = filepath
        self.size_bytes = size_bytes
        self.hash_sha256 = hash_sha256
        self.encrypted = encrypted
        self.compressed = compressed
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.retention_days = retention_days
        self.description = description

    def to_dict(self) -> dict:
        return {
            "backup_id": self.backup_id,
            "source": self.source,
            "filepath": self.filepath,
            "size_bytes": self.size_bytes,
            "hash_sha256": self.hash_sha256,
            "encrypted": self.encrypted,
            "compressed": self.compressed,
            "created_at": self.created_at,
            "retention_days": self.retention_days,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BackupEntry":
        entry = cls(
            backup_id=data["backup_id"],
            source=data["source"],
            filepath=data["filepath"],
            size_bytes=data.get("size_bytes", 0),
            hash_sha256=data.get("hash_sha256", ""),
            encrypted=data.get("encrypted", False),
            compressed=data.get("compressed", False),
            retention_days=data.get("retention_days", 30),
            description=data.get("description", ""),
        )
        entry.created_at = data.get("created_at", entry.created_at)
        return entry
