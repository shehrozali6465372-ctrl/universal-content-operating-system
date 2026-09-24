"""
Backup Manager Module
Layer 1: Core System — Module 10

Comprehensive data protection:
- Multi-source backup (database, memory, logs, configs, prompts, images)
- SHA-256 integrity verification
- Auto backup rotation with retention policy
- Compression support
- Integrity-verified backup/restore (encryption is owned by deployment/storage policy)
- Disaster recovery with restore wizard
- Full audit trail
"""

import json
import gzip
import shutil
import tempfile
import os
import hashlib
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from threading import RLock

from layers.layer01_core.modules.backup_manager.backup_entry import BackupEntry
from layers.layer01_core.modules.backup_manager.exceptions import (
    BackupNotFoundError, BackupIntegrityError,
)


class BackupManager:
    """Full backup and recovery system for the AI Agent."""

    BACKUP_SOURCES = [
        "database", "memory", "logs", "configs",
        "prompts", "images", "settings", "all",
    ]

    def __init__(self, backup_dir: str = "backups", max_backups: int = 50,
                 default_retention_days: int = 30):
        if not isinstance(max_backups, int) or isinstance(max_backups, bool) or max_backups < 1:
            raise ValueError("max_backups must be a positive integer")
        if (
            not isinstance(default_retention_days, int)
            or isinstance(default_retention_days, bool)
            or default_retention_days < 0
        ):
            raise ValueError("default_retention_days must be a non-negative integer")
        self._backup_dir = Path(backup_dir)
        self._backup_dir.mkdir(parents=True, exist_ok=True)
        self._registry_path = self._backup_dir / "_registry.json"
        self._max_backups = max_backups
        self._default_retention_days = default_retention_days
        self._entries: Dict[str, BackupEntry] = {}
        self._lock = RLock()
        self._audit_log: List[dict] = []
        self._counter = 0
        self._load_registry()

    # ── Registry Persistence ─────────────────

    def _load_registry(self) -> None:
        if not self._registry_path.exists():
            return
        try:
            data = json.loads(self._registry_path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                raise ValueError("registry must be a JSON object")
            entries = data.get("entries", {})
            audit_log = data.get("audit_log", [])
            if not isinstance(entries, dict) or not isinstance(audit_log, list):
                raise ValueError("invalid registry structure")
            for key, entry_data in entries.items():
                entry = BackupEntry.from_dict(entry_data)
                if key != entry.backup_id:
                    raise ValueError("registry key does not match backup_id")
                self._safe_backup_path(entry.filepath)
                self._entries[key] = entry
            self._audit_log = audit_log[-200:]
        except (OSError, json.JSONDecodeError, ValueError, TypeError) as exc:
            raise RuntimeError(f"Backup registry is unreadable: {self._registry_path}") from exc

    def _save_registry(self) -> None:
        data = {
            "entries": {k: v.to_dict() for k, v in self._entries.items()},
            "audit_log": self._audit_log[-200:],
        }
        fd, tmp_name = tempfile.mkstemp(dir=str(self._backup_dir), prefix="._registry.", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, default=str)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_name, self._registry_path)
        except Exception:
            try:
                Path(tmp_name).unlink(missing_ok=True)
            except OSError:
                pass
            raise

    def _audit(self, action: str, backup_id: str, details: str = "") -> None:
        entry = {
            "action": action,
            "backup_id": backup_id,
            "details": details,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._audit_log.append(entry)
        if len(self._audit_log) > 200:
            self._audit_log = self._audit_log[-200:]

    def _safe_backup_path(self, relative_path: str) -> Path:
        """Resolve a registry path and require it to remain under backup_dir."""
        candidate = (self._backup_dir / relative_path).resolve()
        try:
            candidate.relative_to(self._backup_dir.resolve())
        except ValueError as exc:
            raise ValueError(f"backup path escapes backup directory: {relative_path}") from exc
        return candidate

    # ── Core: Backup ─────────────────────────

    def backup(self, source: str, source_path: str,
               description: str = "", retention_days: Optional[int] = None,
               compress: bool = True) -> Optional[BackupEntry]:
        """Create a backup of a file or directory."""
        src = Path(source_path)
        if not src.exists():
            return None

        if source not in self.BACKUP_SOURCES:
            source = "all"
        if retention_days is not None and (
            not isinstance(retention_days, int)
            or isinstance(retention_days, bool)
            or retention_days < 0
        ):
            raise ValueError("retention_days must be a non-negative integer")

        with self._lock:
            self._counter += 1
            counter = self._counter
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
        backup_id = f"{source}_{ts}_{counter}"
        backup_filename = f"{backup_id}.bak"
        backup_path = self._backup_dir / backup_filename

        # Stage the copy first. A failed copy must never leave a partially
        # registered backup artifact behind.
        staged_path = self._backup_dir / f".{backup_id}.stage"
        try:
            if src.is_file():
                staged_path = staged_path.with_suffix(".bak.stage")
                shutil.copy2(str(src), str(staged_path))
                os.replace(staged_path, backup_path)
            else:
                staged_path = staged_path.with_suffix(".dir.stage")
                shutil.copytree(str(src), str(staged_path))
                os.replace(staged_path, self._backup_dir / f"{backup_id}.dir")
                backup_path = self._backup_dir / f"{backup_id}.dir"
        except Exception:
            if staged_path.is_dir():
                shutil.rmtree(str(staged_path), ignore_errors=True)
            else:
                staged_path.unlink(missing_ok=True)
            backup_path.unlink(missing_ok=True)
            raise

        # Calculate the hash of the exact uncompressed backup payload.
        file_hash = self._calculate_hash(backup_path)

        # Compress if requested, using a staged container so a failed
        # compression never destroys the valid uncompressed backup.
        final_path = backup_path
        is_compressed = False
        if compress and backup_path.is_file():
            gz_path = Path(str(backup_path) + ".gz")
            fd, tmp_gz = tempfile.mkstemp(dir=str(self._backup_dir), suffix=".gz.tmp")
            os.close(fd)
            try:
                with open(backup_path, "rb") as f_in:
                    with gzip.open(str(tmp_gz), "wb") as f_out:
                        shutil.copyfileobj(f_in, f_out)
                os.replace(tmp_gz, str(gz_path))
            except Exception:
                try:
                    os.unlink(tmp_gz)
                except OSError:
                    pass
                raise
            backup_path.unlink()
            final_path = gz_path
            is_compressed = True
        size = self._get_size(final_path)

        entry = BackupEntry(
            backup_id=backup_id,
            source=source,
            filepath=str(final_path.relative_to(self._backup_dir)),
            size_bytes=size,
            hash_sha256=file_hash,
            compressed=is_compressed,
            retention_days=retention_days if retention_days is not None else self._default_retention_days,
            description=description,
        )

        with self._lock:
            self._entries[backup_id] = entry
            self._audit("CREATE", backup_id, f"source={source}, size={size}")
            self._save_registry()
        return entry

    def backup_json(self, source: str, data: Any,
                    filename: str = "data.json",
                    description: str = "") -> Optional[BackupEntry]:
        """Backup in-memory JSON data using a safe temporary filename."""
        safe_name = Path(filename).name
        if safe_name != filename or safe_name in {"", ".", ".."}:
            raise ValueError("backup JSON filename must be a single path component")
        temp_path = self._backup_dir / f"._temp_{uuid.uuid4().hex}_{safe_name}"
        try:
            temp_path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
            return self.backup(source, str(temp_path), description=description)
        finally:
            temp_path.unlink(missing_ok=True)

    # ── Core: Restore ────────────────────────

    def restore(self, backup_id: str, target_path: str) -> bool:
        """Restore a backup to target path."""
        with self._lock:
            if backup_id not in self._entries:
                raise BackupNotFoundError(f"Backup '{backup_id}' not found")
            entry = self._entries[backup_id]

        backup_file = self._safe_backup_path(entry.filepath)
        if not backup_file.exists():
            raise BackupNotFoundError(f"Backup file not found: {entry.filepath}")

        # Verify integrity
        if not self.verify_integrity(backup_id):
            raise BackupIntegrityError(f"Integrity check failed for '{backup_id}'")

        target = Path(target_path)
        target.parent.mkdir(parents=True, exist_ok=True)

        # Decompress if needed
        temp_dir = Path(tempfile.mkdtemp(dir=str(target.parent), prefix=".restore-"))
        temp_target = temp_dir / target.name
        try:
            if entry.compressed:
                with gzip.open(str(backup_file), "rb") as f_in:
                    with open(str(temp_target), "wb") as f_out:
                        shutil.copyfileobj(f_in, f_out)
            elif backup_file.is_dir():
                shutil.copytree(str(backup_file), str(temp_target), dirs_exist_ok=True)
            else:
                shutil.copy2(str(backup_file), str(temp_target))

            if self._calculate_hash(temp_target) != entry.hash_sha256:
                raise BackupIntegrityError(f"Restored payload verification failed for '{backup_id}'")

            displaced = None
            try:
                if target.exists():
                    displaced = target.parent / f".{target.name}.pre-restore-{uuid.uuid4().hex}"
                    target.replace(displaced)
                temp_target.replace(target)
                temp_target = None
                if displaced is not None:
                    if displaced.is_dir():
                        shutil.rmtree(str(displaced))
                    else:
                        displaced.unlink()
            except Exception:
                if target.exists():
                    if target.is_dir():
                        shutil.rmtree(str(target))
                    else:
                        target.unlink()
                if displaced is not None and displaced.exists():
                    displaced.replace(target)
                raise
        finally:
            # Always remove the staging directory, including after a successful
            # atomic replace where temp_target no longer points at a live path.
            shutil.rmtree(str(temp_dir), ignore_errors=True)

        with self._lock:
            self._audit("RESTORE", backup_id, f"target={target_path}")
            self._save_registry()
        return True

    # ── Integrity ────────────────────────────

    def _calculate_hash(self, filepath: Path) -> str:
        """Hash files or directories deterministically, including file boundaries."""
        sha256 = hashlib.sha256()
        if filepath.is_file():
            with open(filepath, "rb") as f:
                while chunk := f.read(8192):
                    sha256.update(chunk)
            return sha256.hexdigest()

        root = filepath.resolve()
        for f in sorted(root.rglob("*")):
            if not f.is_file():
                continue
            relative = f.relative_to(root).as_posix().encode("utf-8")
            sha256.update(len(relative).to_bytes(8, "big"))
            sha256.update(relative)
            size = f.stat().st_size
            sha256.update(size.to_bytes(8, "big"))
            with open(f, "rb") as fh:
                while chunk := fh.read(8192):
                    sha256.update(chunk)
        return sha256.hexdigest()

    def verify_integrity(self, backup_id: str) -> bool:
        """Verify backup hash matches stored hash."""
        with self._lock:
            if backup_id not in self._entries:
                return False
            entry = self._entries[backup_id]

        backup_file = self._safe_backup_path(entry.filepath)
        if not backup_file.exists():
            return False

        if entry.compressed:
            temp_dir = Path(tempfile.mkdtemp(dir=str(self._backup_dir), prefix=".verify-"))
            try:
                temp_file = temp_dir / "payload"
                try:
                    with gzip.open(str(backup_file), "rb") as src, open(str(temp_file), "wb") as dst:
                        shutil.copyfileobj(src, dst)
                except (OSError, EOFError, gzip.BadGzipFile):
                    return False
                current_hash = self._calculate_hash(temp_file)
            finally:
                shutil.rmtree(str(temp_dir), ignore_errors=True)
        else:
            try:
                current_hash = self._calculate_hash(backup_file)
            except OSError:
                return False
        return current_hash == entry.hash_sha256

    def verify_all(self) -> Dict[str, bool]:
        """Verify integrity of all backups."""
        results = {}
        with self._lock:
            ids = list(self._entries.keys())
        for bid in ids:
            results[bid] = self.verify_integrity(bid)
        return results

    # ── Rotation & Cleanup ───────────────────

    def rotate(self) -> int:
        """Remove expired backups based on retention policy. Returns count removed."""
        removed = 0
        now = datetime.now(timezone.utc)

        with self._lock:
            ids_to_remove = []
            for bid, entry in self._entries.items():
                created = datetime.fromisoformat(entry.created_at)
                age_days = (now - created).days
                if age_days >= entry.retention_days:
                    ids_to_remove.append(bid)

            for bid in ids_to_remove:
                entry = self._entries.pop(bid)
                backup_file = self._safe_backup_path(entry.filepath)
                if backup_file.exists():
                    if backup_file.is_dir():
                        shutil.rmtree(str(backup_file))
                    else:
                        backup_file.unlink()
                removed += 1
                self._audit("ROTATE", bid, "expired")

            # Enforce max_backups limit
            while len(self._entries) > self._max_backups:
                oldest = min(self._entries.items(), key=lambda x: x[1].created_at)
                bid, entry = oldest
                del self._entries[bid]
                backup_file = self._safe_backup_path(entry.filepath)
                if backup_file.exists():
                    if backup_file.is_dir():
                        shutil.rmtree(str(backup_file))
                    else:
                        backup_file.unlink()
                removed += 1
                self._audit("ROTATE", bid, "max_limit")

            self._save_registry()
        return removed

    # ── Listing & Queries ────────────────────

    def list_backups(self, source: Optional[str] = None) -> List[dict]:
        """List all backups, optionally filtered by source."""
        with self._lock:
            entries = list(self._entries.values())
        if source:
            entries = [e for e in entries if e.source == source]
        return [e.to_dict() for e in sorted(entries, key=lambda x: x.created_at)]

    def get_entry(self, backup_id: str) -> BackupEntry:
        with self._lock:
            if backup_id not in self._entries:
                raise BackupNotFoundError(f"Backup '{backup_id}' not found")
            return self._entries[backup_id]

    def delete_backup(self, backup_id: str) -> bool:
        with self._lock:
            if backup_id not in self._entries:
                raise BackupNotFoundError(f"Backup '{backup_id}' not found")
            entry = self._entries.pop(backup_id)
            backup_file = self._safe_backup_path(entry.filepath)
            if backup_file.exists():
                if backup_file.is_dir():
                    shutil.rmtree(str(backup_file))
                else:
                    backup_file.unlink()
            self._audit("DELETE", backup_id)
            self._save_registry()
        return True

    def count(self, source: Optional[str] = None) -> int:
        with self._lock:
            if source:
                return sum(1 for e in self._entries.values() if e.source == source)
            return len(self._entries)

    def total_size(self) -> int:
        with self._lock:
            return sum(e.size_bytes for e in self._entries.values())

    # ── Disaster Recovery ────────────────────

    def disaster_recovery(self, target_dir: str) -> Dict[str, bool]:
        """Restore ALL backups to target directory. Returns {backup_id: success}."""
        results = {}
        with self._lock:
            ids = list(self._entries.keys())

        for bid in ids:
            try:
                entry = self.get_entry(bid)
                sub_dir = Path(target_dir) / entry.source
                sub_dir.mkdir(parents=True, exist_ok=True)
                self.restore(bid, str(sub_dir / entry.filepath))
                results[bid] = True
            except Exception:
                results[bid] = False

        with self._lock:
            self._audit("DISASTER_RECOVERY", "*", f"target={target_dir}")
            self._save_registry()
        return results

    # ── Audit Trail ─────────────────────────

    def get_audit_log(self, limit: int = 50) -> List[dict]:
        with self._lock:
            return list(self._audit_log[-limit:])

    # ── Helpers ──────────────────────────────

    @staticmethod
    def _get_size(filepath: Path) -> int:
        if filepath.is_file():
            return filepath.stat().st_size
        total = 0
        for f in filepath.rglob("*"):
            if f.is_file():
                total += f.stat().st_size
        return total

    # ── Health Check ─────────────────────────

    def health_check(self) -> dict:
        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "checks": {},
            "overall": "PASS",
        }

        with self._lock:
            total = len(self._entries)
            total_size = sum(e.size_bytes for e in self._entries.values())
            sources = set(e.source for e in self._entries.values())
            expired = sum(
                1 for e in self._entries.values()
                if (datetime.now(timezone.utc) - datetime.fromisoformat(e.created_at)).days >= e.retention_days
            )

        report["checks"]["backup_dir"] = {
            "status": "PASS",
            "message": str(self._backup_dir),
        }
        report["checks"]["backups"] = {
            "status": "PASS" if total > 0 else "WARN",
            "message": f"{total} backups, {total_size} bytes",
        }
        report["checks"]["sources"] = {
            "status": "PASS",
            "message": f"{len(sources)} sources: {', '.join(sorted(sources))}" if sources else "No sources",
        }
        report["checks"]["expired"] = {
            "status": "WARN" if expired > 0 else "PASS",
            "message": f"{expired} expired backups pending rotation",
        }

        statuses = [c["status"] for c in report["checks"].values()]
        if "FAIL" in statuses:
            report["overall"] = "FAIL"
        elif "WARN" in statuses:
            report["overall"] = "WARN"
        return report
