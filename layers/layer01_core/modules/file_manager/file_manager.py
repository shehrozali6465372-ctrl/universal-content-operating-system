"""
File Manager Module
Layer 1: Core System — Module 8

Central storage gateway with:
- Safe read/write with atomic operations
- Auto backup before overwrite
- Hash verification (integrity)
- File locking
- Compression support
- In-memory caching
- JSON/CSV import/export
"""

import os
import json
import csv
import shutil
import gzip
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from threading import Lock

from layers.layer01_core.modules.file_manager.hash_utils import calculate_hash, save_hash, verify_hash
from layers.layer01_core.modules.file_manager.file_cache import FileCache


class FileManager:
    """Central storage gateway for the AI Agent."""

    def __init__(self, base_path: str = ".", cache_size: int = 100):
        self._base = Path(base_path)
        self._cache = FileCache(cache_size)
        self._locks: Dict[str, Lock] = {}
        self._global_lock = Lock()

    # ── Safe Read ───────────────────────────

    def read(self, filepath: str, use_cache: bool = True) -> Optional[str]:
        """Read a file safely. Returns None if not found."""
        full = self._resolve(filepath)
        if not full.exists():
            return None
        if use_cache and self._cache.has(str(full)):
            return self._cache.get(str(full))
        content = full.read_text(encoding="utf-8")
        if use_cache:
            self._cache.set(str(full), content)
        return content

    def read_bytes(self, filepath: str) -> Optional[bytes]:
        full = self._resolve(filepath)
        if not full.exists():
            return None
        return full.read_bytes()

    # ── Atomic Write ────────────────────────

    def write(self, filepath: str, content: str, create_backup: bool = True, verify: bool = False) -> bool:
        """Atomic write: temp file → rename. Never half-written."""
        full = self._resolve(filepath)
        full.parent.mkdir(parents=True, exist_ok=True)

        # Auto backup
        if create_backup and full.exists():
            self.backup(filepath)

        # Atomic write via temp file
        fd, tmp_path = tempfile.mkstemp(dir=str(full.parent), suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(content)
            os.replace(tmp_path, str(full))
        except Exception:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise

        # Hash verification
        if verify:
            save_hash(str(full))

        self._cache.invalidate(str(full))
        return True

    def append(self, filepath: str, content: str) -> bool:
        full = self._resolve(filepath)
        full.parent.mkdir(parents=True, exist_ok=True)
        with open(full, "a", encoding="utf-8") as f:
            f.write(content)
        self._cache.invalidate(str(full))
        return True

    # ── File Operations ─────────────────────

    def copy(self, src: str, dst: str) -> bool:
        s, d = self._resolve(src), self._resolve(dst)
        d.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(s), str(d))
        return True

    def move(self, src: str, dst: str) -> bool:
        s, d = self._resolve(src), self._resolve(dst)
        d.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(s), str(d))
        self._cache.invalidate(str(s))
        return True

    def delete(self, filepath: str) -> bool:
        full = self._resolve(filepath)
        if full.exists():
            full.unlink()
            self._cache.invalidate(str(full))
            return True
        return False

    def exists(self, filepath: str) -> bool:
        return self._resolve(filepath).exists()

    def list_files(self, dir_path: str = ".", pattern: str = "*") -> List[str]:
        d = self._resolve(dir_path)
        if not d.exists():
            return []
        return [str(f.relative_to(self._base)) for f in d.glob(pattern) if f.is_file()]

    # ── Backup & Restore ────────────────────

    def backup(self, filepath: str) -> Optional[str]:
        """Create timestamped backup. Returns backup path."""
        full = self._resolve(filepath)
        if not full.exists():
            return None
        backup_dir = self._base / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        backup_name = f"{full.name}.{ts}.bak"
        backup_path = backup_dir / backup_name
        shutil.copy2(str(full), str(backup_path))
        return str(backup_path.relative_to(self._base))

    def restore(self, backup_path: str, target_path: str) -> bool:
        bp = self._resolve(backup_path)
        if not bp.exists():
            return False
        tp = self._resolve(target_path)
        tp.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(bp), str(tp))
        self._cache.invalidate(str(tp))
        return True

    # ── Hash Verification ───────────────────

    def calculate_hash(self, filepath: str) -> Optional[str]:
        full = self._resolve(filepath)
        if not full.exists():
            return None
        return calculate_hash(str(full))

    def verify_hash(self, filepath: str) -> tuple:
        """Returns (match, current_hash)"""
        full = self._resolve(filepath)
        return verify_hash(str(full))

    def save_and_verify(self, filepath: str, content: str) -> bool:
        """Write file with automatic hash save."""
        self.write(filepath, content, create_backup=False)
        save_hash(str(self._resolve(filepath)))
        return True

    # ── Compression ─────────────────────────

    def compress(self, filepath: str) -> Optional[str]:
        """Gzip compress a file. Returns compressed path."""
        full = self._resolve(filepath)
        if not full.exists():
            return None
        gz_path = full.with_suffix(full.suffix + ".gz")
        with open(full, "rb") as f_in:
            with gzip.open(str(gz_path), "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)
        return str(gz_path.relative_to(self._base))

    def decompress(self, gz_path: str) -> Optional[str]:
        """Decompress a gz file."""
        full = self._resolve(gz_path)
        if not full.exists():
            return None
        out_path = full.with_suffix("")  # Remove .gz
        with gzip.open(str(full), "rb") as f_in:
            with open(str(out_path), "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)
        return str(out_path.relative_to(self._base))

    # ── File Lock ───────────────────────────

    def acquire_lock(self, filepath: str) -> Lock:
        with self._global_lock:
            if filepath not in self._locks:
                self._locks[filepath] = Lock()
            return self._locks[filepath]

    # ── Import / Export ─────────────────────

    def export_json(self, filepath: str, data: Any) -> bool:
        return self.write(filepath, json.dumps(data, indent=2, default=str))

    def import_json(self, filepath: str) -> Optional[Any]:
        content = self.read(filepath)
        if content is None:
            return None
        return json.loads(content)

    def export_csv(self, filepath: str, headers: List[str], rows: List[List]) -> bool:
        full = self._resolve(filepath)
        full.parent.mkdir(parents=True, exist_ok=True)
        with open(full, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(rows)
        return True

    def import_csv(self, filepath: str) -> Optional[List[Dict]]:
        content = self.read(filepath)
        if content is None:
            return None
        lines = content.strip().split("\n")
        if len(lines) < 2:
            return []
        headers = lines[0].split(",")
        return [dict(zip(headers, line.split(","))) for line in lines[1:]]

    # ── Cache Stats ─────────────────────────

    def cache_stats(self) -> dict:
        return self._cache.stats()

    # ── Health Check ────────────────────────

    def health_check(self) -> Dict[str, Any]:
        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "checks": {},
            "overall": "PASS",
        }
        report["checks"]["base_path"] = {
            "status": "PASS" if self._base.exists() else "FAIL",
            "message": f"Base: {self._base}",
        }
        report["checks"]["cache"] = {
            "status": "PASS",
            "message": f"{self._cache.size}/{self._cache._max_size} cached, hit rate: {self._cache.hit_rate:.0%}",
        }
        # Check backup dir
        backup_dir = self._base / "backups"
        if backup_dir.exists():
            count = len(list(backup_dir.glob("*.bak")))
            report["checks"]["backups"] = {"status": "PASS", "message": f"{count} backups stored"}
        else:
            report["checks"]["backups"] = {"status": "WARN", "message": "No backup directory"}

        statuses = [c["status"] for c in report["checks"].values()]
        if "FAIL" in statuses:
            report["overall"] = "FAIL"
        elif "WARN" in statuses:
            report["overall"] = "WARN"
        return report

    # ── Internal ────────────────────────────

    def _resolve(self, filepath: str) -> Path:
        return self._base / filepath
