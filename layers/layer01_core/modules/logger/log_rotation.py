"""
Log Rotation Module
Layer 1: Core System — Module 6

Handles log file rotation, compression, and cleanup.
"""

import os
import gzip
import shutil
from pathlib import Path
from typing import Optional
from datetime import datetime, timezone


class LogRotation:
    """Manages log file rotation and compression."""

    def __init__(self, log_dir: str = "logs", max_size_mb: int = 10, max_backups: int = 5):
        self._log_dir = Path(log_dir)
        self._max_size_bytes = max_size_mb * 1024 * 1024
        self._max_backups = max_backups

    @property
    def log_dir(self) -> Path:
        return self._log_dir

    def needs_rotation(self, log_file: str) -> bool:
        """Check if a log file needs rotation."""
        path = self._log_dir / log_file
        if not path.exists():
            return False
        return path.stat().st_size >= self._max_size_bytes

    def rotate(self, log_file: str) -> Optional[Path]:
        """Rotate a log file. Returns backup path or None."""
        path = self._log_dir / log_file
        if not path.exists() or not self.needs_rotation(log_file):
            return None

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        backup_name = f"{log_file}.{timestamp}.gz"
        backup_path = self._log_dir / backup_name

        # Compress and move
        with open(path, "rb") as f_in:
            with gzip.open(backup_path, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)

        # Truncate original
        path.write_text("")

        # Clean old backups
        self._cleanup_old_backups(log_file)
        return backup_path

    def _cleanup_old_backups(self, log_file: str) -> None:
        """Remove old backups beyond max_backups limit."""
        pattern = f"{log_file}."
        backups = sorted(
            [f for f in self._log_dir.iterdir() if f.name.startswith(pattern) and f.name.endswith(".gz")],
            key=lambda f: f.stat().st_mtime,
        )
        while len(backups) > self._max_backups:
            oldest = backups.pop(0)
            oldest.unlink()

    def get_backups(self, log_file: str) -> list:
        """List backups for a log file."""
        pattern = f"{log_file}."
        return sorted(
            [f for f in self._log_dir.iterdir() if f.name.startswith(pattern) and f.name.endswith(".gz")],
            key=lambda f: f.stat().st_mtime,
            reverse=True,
        )

    def get_log_size(self, log_file: str) -> int:
        """Get current log file size in bytes."""
        path = self._log_dir / log_file
        return path.stat().st_size if path.exists() else 0

    def get_total_size(self) -> int:
        """Get total size of all log files."""
        if not self._log_dir.exists():
            return 0
        return sum(f.stat().st_size for f in self._log_dir.iterdir() if f.is_file())
