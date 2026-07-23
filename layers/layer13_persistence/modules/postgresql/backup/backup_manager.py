"""BackupManager — Database backup, restore, and verification.

Supports full table backup to JSON with integrity verification.
"""
from __future__ import annotations
import json
import os
import time
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone


class BackupManager:
    """Manage database backups and restores."""

    def __init__(self, pool: Any, backup_dir: str = "backups"):
        self._pool = pool
        self._backup_dir = backup_dir
        os.makedirs(backup_dir, exist_ok=True)

    def backup(self, name: Optional[str] = None) -> Dict[str, Any]:
        """Dump all tables to a JSON file."""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = name or f"backup_{timestamp}.json"
        filepath = os.path.join(self._backup_dir, filename)

        data = {"timestamp": time.time(), "tables": {}}
        tables = self._pool.get_tables()
        total_rows = 0

        for table in tables:
            try:
                rows = self._pool.query(f"SELECT * FROM {table}")
                data["tables"][table] = rows
                total_rows += len(rows)
            except Exception:
                data["tables"][table] = []

        data["total_rows"] = total_rows
        data["table_count"] = len(data["tables"])

        with open(filepath, "w") as f:
            json.dump(data, f, indent=2, default=str)

        return {
            "filepath": filepath,
            "filename": filename,
            "table_count": len(data["tables"]),
            "total_rows": total_rows,
            "size_bytes": os.path.getsize(filepath),
        }

    def restore(self, filepath: str) -> Dict[str, Any]:
        """Load data from JSON backup file."""
        with open(filepath, "r") as f:
            data = json.load(f)

        restored_tables = 0
        restored_rows = 0

        for table_name, rows in data.get("tables", {}).items():
            if not rows:
                continue
            try:
                # Clear existing data
                self._pool.delete(table_name, "1=1")
                # Insert backed up rows
                for row in rows:
                    # Remove id columns that may auto-increment
                    clean = {k: v for k, v in row.items() if k not in ("id",)}
                    if clean:
                        self._pool.insert(table_name, clean)
                        restored_rows += 1
                restored_tables += 1
            except Exception:
                pass

        return {
            "restored_tables": restored_tables,
            "restored_rows": restored_rows,
            "source_timestamp": data.get("timestamp"),
        }

    def verify_backup(self, filepath: str) -> Dict[str, Any]:
        """Check backup file integrity."""
        with open(filepath, "r") as f:
            data = json.load(f)

        issues = []
        tables = data.get("tables", {})

        if not tables:
            issues.append("No tables in backup")

        for name, rows in tables.items():
            if not isinstance(rows, list):
                issues.append(f"Table {name}: invalid format")

        return {
            "valid": len(issues) == 0,
            "table_count": len(tables),
            "total_rows": data.get("total_rows", 0),
            "issues": issues,
            "timestamp": data.get("timestamp"),
        }

    def list_backups(self) -> List[Dict[str, Any]]:
        """List available backup files."""
        backups = []
        if not os.path.exists(self._backup_dir):
            return backups
        for f in sorted(os.listdir(self._backup_dir)):
            if f.endswith(".json"):
                path = os.path.join(self._backup_dir, f)
                stat = os.stat(path)
                backups.append({
                    "filename": f,
                    "filepath": path,
                    "size_bytes": stat.st_size,
                    "modified": stat.st_mtime,
                })
        return backups

    def auto_backup(self) -> Dict[str, Any]:
        """Create a timestamped backup."""
        return self.backup()
