"""
Memory Manager Module
Layer 1: Core System — Module 5

4-level memory system for AI Agent:
- Short-Term (STM): Current task, conversation, session
- Working: Active goals, plans, decisions
- Long-Term (LTM): Brand voice, patterns, strategies
- Episodic: History, mistakes, improvements

Designed with swappable backend (SQLite → Vector DB later).
"""

import sqlite3
import os
import json
import math
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from threading import RLock
import tempfile

from layers.layer01_core.modules.memory_store import (
    MemoryLevel, get_level_config, get_persistent_levels,
)
from layers.layer01_core.modules.memory_search import (
    MemorySearchEngine, SearchQuery, SearchResult,
)


class MemoryManager:
    """4-level memory system with search, compression, and snapshots."""

    def __init__(self, db_path: str = "data/agent_memory.db", project_root: Optional[str] = None):
        self._project_root = Path(project_root) if project_root else Path.cwd()
        self._db_path = (self._project_root / db_path).resolve()
        try:
            self._db_path.relative_to(self._project_root.resolve())
        except ValueError as exc:
            raise ValueError(f"Memory database path escapes project root: {db_path}") from exc
        self._conn: Optional[sqlite3.Connection] = None
        self._lock = RLock()
        self._search_engine = MemorySearchEngine()
        self._stm_buffer: List[Dict] = []  # RAM buffer for short-term
        self._stm_sequence = int(time.time() * 1000) % 2_000_000_000
        self._initialized = False

    @property
    def is_initialized(self) -> bool:
        return self._initialized

    # ── Initialization ──────────────────────

    def initialize(self) -> "MemoryManager":
        """Create the development/test local store; production memory belongs to Layer 13."""
        with self._lock:
            if self._initialized and self._conn is not None:
                return self
            if os.environ.get("APP_ENV", "development").lower() in {"production", "prod"}:
                raise RuntimeError(
                    "Layer 1 local memory persistence is development/test-only; production memory is owned by Layer 13"
                )
            self._db_path.parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(str(self._db_path), check_same_thread=False, timeout=30.0)
            try:
                conn.row_factory = sqlite3.Row
                self._conn = conn
                self._create_tables()
            except Exception:
                conn.close()
                self._conn = None
                self._initialized = False
                raise
            self._initialized = True
            return self

    def _create_tables(self) -> None:
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS memory_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                level TEXT NOT NULL,
                category TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                tags TEXT DEFAULT '',
                importance REAL DEFAULT 0.5,
                access_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_memory_level ON memory_entries(level);
            CREATE INDEX IF NOT EXISTS idx_memory_category ON memory_entries(category);
            CREATE INDEX IF NOT EXISTS idx_memory_key ON memory_entries(key);
        """)
        self._conn.commit()

    def close(self) -> None:
        with self._lock:
            if self._conn:
                self._conn.close()
                self._conn = None
                self._initialized = False

    # ── Save (CRUD) ────────────────────────

    def save(
        self,
        level: str,
        category: str,
        key: str,
        value: str,
        tags: str = "",
        importance: float = 0.5,
    ) -> int:
        """Save a memory entry. Returns entry ID."""
        self._ensure_init()
        level = self._normalize_level(level)
        self._validate_entry(level, category, key, value, importance)
        if not isinstance(tags, str):
            raise TypeError("Memory tags must be a string")
        with self._lock:
            return self._save_locked(level, category, key, value, tags, importance)

    @staticmethod
    def _normalize_level(level: str) -> str:
        aliases = {
            "stm": MemoryLevel.STM.value,
            "working": MemoryLevel.WORKING.value,
            "ltm": MemoryLevel.LTM.value,
            "episodic": MemoryLevel.EPISODIC.value,
        }
        if not isinstance(level, str):
            raise TypeError("Memory level must be a string")
        normalized = aliases.get(level.strip().lower(), level.strip().lower())
        if normalized not in {member.value for member in MemoryLevel}:
            raise ValueError(f"Invalid memory level: {level}")
        return normalized

    @staticmethod
    def _validate_entry(
        level: str,
        category: str,
        key: str,
        value: str,
        importance: float,
    ) -> None:
        allowed_levels = {member.value for member in MemoryLevel}
        if level not in allowed_levels:
            raise ValueError(f"Invalid memory level: {level}")
        if not isinstance(category, str) or not category.strip():
            raise ValueError("Memory category cannot be empty")
        if not isinstance(key, str) or not key.strip():
            raise ValueError("Memory key cannot be empty")
        if not isinstance(value, str):
            raise TypeError("Memory value must be a string")
        if not isinstance(importance, (int, float)) or isinstance(importance, bool):
            raise TypeError("Memory importance must be numeric")
        if not math.isfinite(float(importance)) or not 0.0 <= float(importance) <= 1.0:
            raise ValueError("Memory importance must be between 0 and 1")

    def _save_locked(self, level: str, category: str, key: str, value: str, tags: str, importance: float) -> int:
        # STM goes to RAM buffer
        if level == MemoryLevel.STM.value:
            entry = {
                "level": level, "category": category, "key": key,
                "value": value, "tags": tags, "importance": importance,
                "access_count": 0,
                "id": self._next_stm_id(),
            }
            self._stm_buffer.append(entry)
            self._enforce_stm_limit()
            return entry["id"]

        # Persistent levels go to DB
        with self._conn:
            cursor = self._conn.execute(
                """INSERT INTO memory_entries (level, category, key, value, tags, importance)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (level, category, key, value, tags, importance),
            )
            return cursor.lastrowid

    def save_batch(self, entries: List[Dict[str, Any]]) -> int:
        """Save multiple entries at once. Returns count saved."""
        self._ensure_init()
        if not entries:
            return 0
        with self._lock:
            original_stm = list(self._stm_buffer)
            persistent = []
            try:
                for entry in entries:
                    level = self._normalize_level(entry.get("level", "long_term"))
                    category = entry.get("category", "general")
                    key = entry.get("key", "")
                    value = entry.get("value", "")
                    importance = entry.get("importance", 0.5)
                    self._validate_entry(level, category, key, value, importance)
                    if not isinstance(entry.get("tags", ""), str):
                        raise TypeError("Memory tags must be a string")
                    if level == MemoryLevel.STM.value:
                        self._save_locked(
                            level, entry.get("category", "general"),
                            entry.get("key", ""), entry.get("value", ""),
                            entry.get("tags", ""), entry.get("importance", 0.5),
                        )
                    else:
                        persistent.append((
                            level, entry.get("category", "general"),
                            entry.get("key", ""), entry.get("value", ""),
                            entry.get("tags", ""), entry.get("importance", 0.5),
                        ))
                if persistent:
                    with self._conn:
                        self._conn.executemany(
                            "INSERT INTO memory_entries "
                            "(level, category, key, value, tags, importance) "
                            "VALUES (?, ?, ?, ?, ?, ?)",
                            persistent,
                        )
                return len(entries)
            except Exception:
                self._stm_buffer = original_stm
                raise

    # ── Load ────────────────────────────────

    def load(self, level: str, category: str = "", key: str = "") -> List[Dict]:
        """Load memory entries with optional filters."""
        self._ensure_init()
        level = self._normalize_level(level)

        with self._lock:
            if level == MemoryLevel.STM.value:
                results = list(self._stm_buffer)
                if category:
                    results = [e for e in results if e.get("category") == category]
                if key:
                    results = [e for e in results if e.get("key") == key]
                return [dict(e) for e in results]

            sql = "SELECT * FROM memory_entries WHERE level = ?"
            params: list = [level]
            if category:
                sql += " AND category = ?"
                params.append(category)
            if key:
                sql += " AND key = ?"
                params.append(key)
            sql += " ORDER BY importance DESC, updated_at DESC"
            return [dict(r) for r in self._conn.execute(sql, params).fetchall()]

    def get(self, entry_id: int) -> Optional[Dict]:
        """Get single entry by ID."""
        self._ensure_init()
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM memory_entries WHERE id = ?", (entry_id,)
            ).fetchone()
            if row:
                self._conn.execute(
                    "UPDATE memory_entries SET access_count = access_count + 1, "
                    "last_accessed = CURRENT_TIMESTAMP WHERE id = ?",
                    (entry_id,),
                )
                self._conn.commit()
                result = dict(row)
                result["access_count"] = result.get("access_count", 0) + 1
                return result
            return None

    # ── Update ──────────────────────────────

    def update(self, entry_id: int, **kwargs) -> bool:
        """Update fields of a memory entry."""
        self._ensure_init()
        allowed = {"category", "key", "value", "tags", "importance"}
        updates = {k: v for k, v in kwargs.items() if k in allowed}
        if not updates:
            return False
        with self._lock:
            current = self._conn.execute(
                "SELECT level, category, key, value, importance FROM memory_entries WHERE id = ?",
                (entry_id,),
            ).fetchone()
        if current is None:
            return False
        candidate = {
            "category": updates.get("category", current["category"]),
            "key": updates.get("key", current["key"]),
            "value": updates.get("value", current["value"]),
            "importance": updates.get("importance", current["importance"]),
        }
        self._validate_entry(
            current["level"],
            candidate["category"],
            candidate["key"],
            candidate["value"],
            candidate["importance"],
        )
        if "tags" in updates and not isinstance(updates["tags"], str):
            raise TypeError("Memory tags must be a string")
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        with self._lock:
            with self._conn:
                self._conn.execute(
                    f"UPDATE memory_entries SET {set_clause} WHERE id = ?",
                    list(updates.values()) + [entry_id],
                )
        return True

    # ── Delete ──────────────────────────────

    def delete(self, entry_id: int) -> bool:
        self._ensure_init()
        with self._lock:
            with self._conn:
                cursor = self._conn.execute("DELETE FROM memory_entries WHERE id = ?", (entry_id,))
                return cursor.rowcount > 0

    def clear_level(self, level: str) -> int:
        """Clear all entries for a memory level."""
        self._ensure_init()
        level = self._normalize_level(level)
        with self._lock:
            if level == MemoryLevel.STM.value:
                count = len(self._stm_buffer)
                self._stm_buffer.clear()
                return count
            with self._conn:
                cursor = self._conn.execute("DELETE FROM memory_entries WHERE level = ?", (level,))
                return cursor.rowcount

    # ── Search ──────────────────────────────

    def search(
        self,
        keyword: str = "",
        levels: List[str] = None,
        tags: List[str] = None,
        category: str = "",
        limit: int = 20,
    ) -> List[SearchResult]:
        """Search across all memory levels."""
        if not isinstance(limit, int) or not 1 <= limit <= 1000:
            raise ValueError("search limit must be between 1 and 1000")
        normalized_levels = [self._normalize_level(level) for level in (levels or [])]
        query = SearchQuery(
            keyword=keyword,
            levels=normalized_levels,
            tags=tags or [],
            category=category,
            limit=limit,
        )
        all_entries = self._get_all_entries()
        return self._search_engine.search(all_entries, query)

    def find_by_key(self, key: str) -> Optional[Dict]:
        """Find first entry matching key across all levels."""
        all_entries = self._get_all_entries()
        return self._search_engine.find_by_key(all_entries, key)

    # ── Compression ─────────────────────────

    def compress_level(self, level: str) -> int:
        """Compress a memory level by removing low-importance duplicates."""
        self._ensure_init()
        normalized_level = self._normalize_level(level)
        config = get_level_config(MemoryLevel(normalized_level))
        entries = self.load(normalized_level)
        if len(entries) <= config.max_entries:
            return 0

        # Sort by importance, keep top N
        entries.sort(key=lambda e: e.get("importance", 0), reverse=True)
        to_remove = entries[config.max_entries:]

        removed = 0
        for entry in to_remove:
            if "id" in entry:
                self.delete(entry["id"])
                removed += 1
        return removed

    # ── Snapshot ────────────────────────────

    def snapshot(self, filepath: str = "data/memory_snapshot.json") -> Path:
        """Export all persistent memory to JSON."""
        self._ensure_init()
        save_path = (self._project_root / filepath).resolve()
        try:
            save_path.relative_to(self._project_root.resolve())
        except ValueError as exc:
            raise ValueError(f"Memory snapshot path escapes project root: {filepath}") from exc
        save_path.parent.mkdir(parents=True, exist_ok=True)

        with self._lock:
            snapshot = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "levels": {},
            }
            for level in get_persistent_levels():
                rows = self._conn.execute(
                    "SELECT * FROM memory_entries WHERE level = ? "
                    "ORDER BY importance DESC, updated_at DESC",
                    (level.value,),
                ).fetchall()
                entries = [dict(row) for row in rows]
                snapshot["levels"][level.value] = {
                    "count": len(entries),
                    "entries": entries,
                }

            fd, tmp_name = tempfile.mkstemp(dir=str(save_path.parent), suffix=".snapshot.tmp")
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    json.dump(snapshot, f, indent=2, default=str)
                    f.flush()
                    os.fsync(f.fileno())
                os.replace(tmp_name, save_path)
            except Exception:
                try:
                    os.unlink(tmp_name)
                except OSError:
                    pass
                raise
        return save_path

    def restore(self, filepath: str) -> int:
        """Atomically replace persistent memory from a validated snapshot."""
        self._ensure_init()
        snap_path = (self._project_root / filepath).resolve()
        try:
            snap_path.relative_to(self._project_root.resolve())
        except ValueError as exc:
            raise ValueError(f"Memory snapshot path escapes project root: {filepath}") from exc
        with open(snap_path, encoding="utf-8") as f:
            snapshot = json.load(f)
        if not isinstance(snapshot, dict) or not isinstance(snapshot.get("levels", {}), dict):
            raise ValueError("Invalid memory snapshot format")

        rows = []
        allowed_levels = {level.value for level in get_persistent_levels()}
        for level_name, level_data in snapshot["levels"].items():
            if level_name not in allowed_levels or not isinstance(level_data, dict):
                raise ValueError(f"Invalid memory level in snapshot: {level_name}")
            entries = level_data.get("entries", [])
            declared_count = level_data.get("count")
            if not isinstance(entries, list) or not isinstance(declared_count, int) or declared_count != len(entries):
                raise ValueError("Memory snapshot count mismatch")
            for entry in entries:
                if not isinstance(entry, dict):
                    raise ValueError("Invalid memory entry in snapshot")
                entry_level = entry.get("level", level_name)
                if entry_level != level_name or entry_level not in allowed_levels:
                    raise ValueError("Memory snapshot entry level mismatch")
                category = entry.get("category", "general")
                key = entry.get("key", "")
                value = entry.get("value", "")
                tags = entry.get("tags", "")
                importance = entry.get("importance", 0.5)
                self._validate_entry(entry_level, category, key, value, importance)
                if not isinstance(tags, str):
                    raise TypeError("Memory snapshot tags must be a string")
                rows.append((
                    entry_level, category, key, value, tags, importance,
                ))

        with self._lock:
            try:
                with self._conn:
                    for level in allowed_levels:
                        self._conn.execute(
                            "DELETE FROM memory_entries WHERE level = ?", (level,)
                        )
                    if rows:
                        self._conn.executemany(
                            "INSERT INTO memory_entries "
                            "(level, category, key, value, tags, importance) "
                            "VALUES (?, ?, ?, ?, ?, ?)",
                            rows,
                        )
            except Exception:
                raise
        return len(rows)

    # ── Health Check ────────────────────────

    def health_check(self) -> Dict[str, Any]:
        self._ensure_init()
        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "checks": {},
            "overall": "PASS",
        }

        # Check 1: Connection and entry counts under one connection lock.
        try:
            with self._lock:
                self._conn.execute("SELECT 1")
                report["checks"]["connection"] = {"status": "PASS", "message": "Connected"}
                counts = {}
                for level in MemoryLevel:
                    if level == MemoryLevel.STM:
                        counts[level.value] = len(self._stm_buffer)
                    else:
                        cursor = self._conn.execute(
                            "SELECT COUNT(*) as c FROM memory_entries WHERE level = ?", (level.value,)
                        )
                        counts[level.value] = cursor.fetchone()["c"]
        except Exception as e:
            report["checks"]["connection"] = {"status": "FAIL", "message": str(e)}
            report["overall"] = "FAIL"
            return report
        report["checks"]["entry_counts"] = {"status": "PASS", "message": str(counts)}

        # Check 3: STM overflow warning
        stm_config = get_level_config(MemoryLevel.STM)
        if len(self._stm_buffer) > stm_config.max_entries * 0.9:
            report["checks"]["stm_usage"] = {
                "status": "WARN",
                "message": f"STM at {len(self._stm_buffer)}/{stm_config.max_entries} capacity",
            }
        else:
            report["checks"]["stm_usage"] = {
                "status": "PASS",
                "message": f"STM: {len(self._stm_buffer)}/{stm_config.max_entries}",
            }

        # Overall
        statuses = [c["status"] for c in report["checks"].values()]
        if "FAIL" in statuses:
            report["overall"] = "FAIL"
        elif "WARN" in statuses:
            report["overall"] = "WARN"

        return report

    # ── Stats ───────────────────────────────

    def get_stats(self) -> Dict[str, Any]:
        self._ensure_init()
        with self._lock:
            stats = {"levels": {}, "total_persistent": 0, "stm_buffer": len(self._stm_buffer)}
            for level in MemoryLevel:
                if level == MemoryLevel.STM:
                    count = len(self._stm_buffer)
                else:
                    cursor = self._conn.execute(
                        "SELECT COUNT(*) as c FROM memory_entries WHERE level = ?", (level.value,)
                    )
                    count = cursor.fetchone()["c"]
                config = get_level_config(level)
                stats["levels"][level.value] = {
                    "count": count,
                    "max": config.max_entries,
                    "utilization": f"{(count / config.max_entries * 100):.1f}%",
                }
                stats["total_persistent"] += count
            return stats

    # ── Internal ────────────────────────────

    def _update_access(self, entry_id: int) -> None:
        with self._conn:
            self._conn.execute(
                """UPDATE memory_entries SET access_count = access_count + 1,
                   last_accessed = CURRENT_TIMESTAMP WHERE id = ?""",
                (entry_id,),
            )

    def _next_stm_id(self) -> int:
        """Return a process-local monotonic STM id to avoid millisecond collisions."""
        self._stm_sequence += 1
        return self._stm_sequence

    def _enforce_stm_limit(self) -> None:
        config = get_level_config(MemoryLevel.STM)
        if len(self._stm_buffer) > config.max_entries:
            self._stm_buffer = self._stm_buffer[-config.max_entries:]

    def _get_all_entries(self) -> List[Dict]:
        self._ensure_init()
        # STM from buffer
        with self._lock:
            all_entries = [dict(e) for e in self._stm_buffer]
            rows = self._conn.execute("SELECT * FROM memory_entries LIMIT 10000").fetchall()
            all_entries.extend([dict(r) for r in rows])
            return all_entries

    def _ensure_init(self):
        if not self._initialized:
            raise RuntimeError("MemoryManager not initialized. Call initialize() first.")
