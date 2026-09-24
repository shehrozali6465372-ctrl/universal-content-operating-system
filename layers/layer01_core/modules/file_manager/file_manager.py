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
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from io import StringIO
from datetime import datetime, timezone
from threading import Lock, RLock

from layers.layer01_core.modules.file_manager.hash_utils import calculate_hash, save_hash, verify_hash
from layers.layer01_core.modules.file_manager.file_cache import FileCache

logger = logging.getLogger(__name__)


class FileManager:
    """Central storage gateway for the AI Agent."""

    def __init__(self, base_path: str = ".", cache_size: int = 100):
        self._base = Path(base_path).resolve()
        self._cache = FileCache(cache_size)
        # Strong references are required: a returned lock may outlive this lookup.
        self._locks: Dict[str, Lock] = {}
        self._global_lock = RLock()

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
        with self._global_lock:
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
                    f.flush()
                    os.fsync(f.fileno())
                os.replace(tmp_path, str(full))
            except Exception:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
                raise

            # A content replacement invalidates any previous integrity metadata.
            # Recreate it only when the caller explicitly requests verification.
            hash_path = Path(str(full) + ".sha256")
            if verify:
                save_hash(str(full))
            elif hash_path.exists():
                hash_path.unlink()

            self._cache.invalidate(str(full))
            return True

    def append(self, filepath: str, content: str) -> bool:
        """Atomically append content while serializing concurrent writers."""
        full = self._resolve(filepath)
        with self._global_lock:
            existing = full.read_text(encoding="utf-8") if full.exists() else ""
            return self.write(filepath, existing + content, create_backup=False)

    # ── File Operations ─────────────────────

    def copy(self, src: str, dst: str) -> bool:
        with self._global_lock:
            s, d = self._resolve(src), self._resolve(dst)
            d.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(s), str(d))
            src_hash = Path(str(s) + ".sha256")
            dst_hash = Path(str(d) + ".sha256")
            if src_hash.exists():
                shutil.copy2(str(src_hash), str(dst_hash))
            elif dst_hash.exists():
                dst_hash.unlink()
            self._cache.invalidate(str(d))
            return True

    def move(self, src: str, dst: str) -> bool:
        with self._global_lock:
            s, d = self._resolve(src), self._resolve(dst)
            d.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(s), str(d))
            src_hash, dst_hash = Path(str(s) + ".sha256"), Path(str(d) + ".sha256")
            if src_hash.exists():
                shutil.move(str(src_hash), str(dst_hash))
            elif dst_hash.exists():
                dst_hash.unlink()
            self._cache.invalidate(str(s))
            self._cache.invalidate(str(d))
            return True

    def delete(self, filepath: str) -> bool:
        with self._global_lock:
            full = self._resolve(filepath)
            if full.exists():
                full.unlink()
                hash_file = Path(str(full) + ".sha256")
                if hash_file.exists():
                    hash_file.unlink()
                self._cache.invalidate(str(full))
                return True
            return False

    def exists(self, filepath: str) -> bool:
        return self._resolve(filepath).exists()

    def list_files(self, dir_path: str = ".", pattern: str = "*") -> List[str]:
        if not isinstance(pattern, str) or not pattern or any(sep in pattern for sep in ("/", "\\")):
            raise ValueError("file glob pattern must not contain path separators")
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
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
        backup_name = f"{full.name}.{ts}.bak"
        backup_path = backup_dir / backup_name
        shutil.copy2(str(full), str(backup_path))
        save_hash(str(backup_path))
        return str(backup_path.relative_to(self._base))

    def restore(self, backup_path: str, target_path: str) -> bool:
        """Restore only after verifying the staged payload, with rollback safety."""
        with self._global_lock:
            bp = self._resolve(backup_path)
            if not bp.exists():
                return False
            tp = self._resolve(target_path)
            ok, expected_hash = verify_hash(str(bp))
            if not ok or expected_hash is None:
                raise ValueError("Backup integrity verification failed")

            tp.parent.mkdir(parents=True, exist_ok=True)
            fd, tmp_name = tempfile.mkstemp(dir=str(tp.parent), suffix=".restore.tmp")
            os.close(fd)
            displaced = None
            try:
                shutil.copy2(str(bp), tmp_name)
                if calculate_hash(tmp_name) != expected_hash:
                    raise ValueError("Backup integrity verification failed during restore")
                if tp.exists():
                    displaced = tp.parent / f".{tp.name}.pre-restore.tmp"
                    os.replace(str(tp), str(displaced))
                os.replace(tmp_name, str(tp))
                tmp_name = None
                save_hash(str(tp))
                if displaced is not None and displaced.exists():
                    displaced.unlink()
            except Exception:
                if os.path.exists(tmp_name):
                    try:
                        os.unlink(tmp_name)
                    except OSError:
                        pass
                if displaced is not None and displaced.exists() and not tp.exists():
                    os.replace(str(displaced), str(tp))
                raise
            finally:
                if displaced is not None and displaced.exists():
                    try:
                        displaced.unlink()
                    except OSError:
                        pass
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
        fd, tmp_name = tempfile.mkstemp(dir=str(gz_path.parent), suffix=".gz.tmp")
        os.close(fd)
        try:
            with open(full, "rb") as f_in:
                with gzip.open(tmp_name, "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)
            os.replace(tmp_name, str(gz_path))
        except Exception:
            try:
                os.unlink(tmp_name)
            except OSError:
                pass
            raise
        return str(gz_path.relative_to(self._base))

    def decompress(self, gz_path: str) -> Optional[str]:
        """Decompress a gz file."""
        full = self._resolve(gz_path)
        if not full.exists():
            return None
        out_path = full.with_suffix("")
        fd, tmp_name = tempfile.mkstemp(dir=str(out_path.parent), suffix=".decompress.tmp")
        os.close(fd)
        try:
            with gzip.open(str(full), "rb") as f_in:
                with open(tmp_name, "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)
                    f_out.flush()
                    os.fsync(f_out.fileno())
            os.replace(tmp_name, str(out_path))
        except Exception:
            try:
                os.unlink(tmp_name)
            except OSError:
                pass
            raise
        self._cache.invalidate(str(out_path))
        return str(out_path.relative_to(self._base))

    # ── File Lock ───────────────────────────

    def acquire_lock(self, filepath: str) -> Lock:
        """Return a stable per-path lock for the lifetime of this manager."""
        full = self._resolve(filepath)
        key = str(full)
        with self._global_lock:
            if key not in self._locks:
                self._locks[key] = Lock()
            return self._locks[key]

    def release_lock(self, filepath: str) -> None:
        """Drop an unused per-path lock from the lock registry."""
        full = self._resolve(filepath)
        key = str(full)
        with self._global_lock:
            lock = self._locks.get(key)
            if lock is not None and not lock.locked():
                self._locks.pop(key, None)

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
        output = StringIO(newline="")
        writer = csv.writer(output)
        writer.writerow(headers)
        writer.writerows(rows)
        return self.write(filepath, output.getvalue(), create_backup=False)

    def import_csv(self, filepath: str) -> Optional[List[Dict]]:
        content = self.read(filepath)
        if content is None:
            return None
        if not content.strip():
            return []
        return [dict(row) for row in csv.DictReader(StringIO(content))]

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
        """Resolve a path and enforce the FileManager storage boundary."""
        base = self._base.resolve()
        candidate = (self._base / filepath).resolve()
        try:
            candidate.relative_to(base)
        except ValueError as exc:
            raise ValueError(f"Path escapes FileManager base directory: {filepath}") from exc
        return candidate
