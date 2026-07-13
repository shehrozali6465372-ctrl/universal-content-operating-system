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
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone

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
        self._db_path = self._project_root / db_path
        self._conn: Optional[sqlite3.Connection] = None
        self._search_engine = MemorySearchEngine()
        self._stm_buffer: List[Dict] = []  # RAM buffer for short-term
        self._initialized = False

    @property
    def is_initialized(self) -> bool:
        return self._initialized

    # ── Initialization ──────────────────────

    def initialize(self) -> "MemoryManager":
        """Create database and tables."""
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self._db_path))
        self._conn.row_factory = sqlite3.Row
        self._create_tables()
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

        # STM goes to RAM buffer
        if level == MemoryLevel.STM.value:
            entry = {
                "level": level, "category": category, "key": key,
                "value": value, "tags": tags, "importance": importance,
                "access_count": 0, "id": int(time.time() * 1000) % 100000,
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
        count = 0
        for entry in entries:
            self.save(
                level=entry.get("level", "long_term"),
                category=entry.get("category", "general"),
                key=entry.get("key", ""),
                value=entry.get("value", ""),
                tags=entry.get("tags", ""),
                importance=entry.get("importance", 0.5),
            )
            count += 1
        return count

    # ── Load ────────────────────────────────

    def load(self, level: str, category: str = "", key: str = "") -> List[Dict]:
        """Load memory entries with optional filters."""
        self._ensure_init()

        if level == MemoryLevel.STM.value:
            results = self._stm_buffer
            if category:
                results = [e for e in results if e.get("category") == category]
            if key:
                results = [e for e in results if e.get("key") == key]
            return results

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
        row = self._conn.execute(
            "SELECT * FROM memory_entries WHERE id = ?", (entry_id,)
        ).fetchone()
        if row:
            self._update_access(entry_id)
            return dict(row)
        return None

    # ── Update ──────────────────────────────

    def update(self, entry_id: int, **kwargs) -> bool:
        """Update fields of a memory entry."""
        self._ensure_init()
        allowed = {"category", "key", "value", "tags", "importance"}
        updates = {k: v for k, v in kwargs.items() if k in allowed}
        if not updates:
            return False
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        with self._conn:
            self._conn.execute(
                f"UPDATE memory_entries SET {set_clause} WHERE id = ?",
                list(updates.values()) + [entry_id],
            )
        return True

    # ── Delete ──────────────────────────────

    def delete(self, entry_id: int) -> bool:
        self._ensure_init()
        with self._conn:
            cursor = self._conn.execute("DELETE FROM memory_entries WHERE id = ?", (entry_id,))
            return cursor.rowcount > 0

    def clear_level(self, level: str) -> int:
        """Clear all entries for a memory level."""
        self._ensure_init()
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
        query = SearchQuery(
            keyword=keyword,
            levels=levels or [],
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
        config = get_level_config(MemoryLevel(level))
        entries = self.load(level)
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
        save_path = self._project_root / filepath
        save_path.parent.mkdir(parents=True, exist_ok=True)

        snapshot = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "levels": {},
        }
        for level in get_persistent_levels():
            entries = self.load(level.value)
            snapshot["levels"][level.value] = {
                "count": len(entries),
                "entries": entries,
            }

        with open(save_path, "w") as f:
            json.dump(snapshot, f, indent=2, default=str)
        return save_path

    def restore(self, filepath: str) -> int:
        """Restore memory from a snapshot."""
        self._ensure_init()
        snap_path = self._project_root / filepath
        with open(snap_path) as f:
            snapshot = json.load(f)

        count = 0
        for level_name, level_data in snapshot.get("levels", {}).items():
            for entry in level_data.get("entries", []):
                self.save(
                    level=entry.get("level", level_name),
                    category=entry.get("category", "general"),
                    key=entry.get("key", ""),
                    value=entry.get("value", ""),
                    tags=entry.get("tags", ""),
                    importance=entry.get("importance", 0.5),
                )
                count += 1
        return count

    # ── Health Check ────────────────────────

    def health_check(self) -> Dict[str, Any]:
        self._ensure_init()
        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "checks": {},
            "overall": "PASS",
        }

        # Check 1: Connection
        try:
            self._conn.execute("SELECT 1")
            report["checks"]["connection"] = {"status": "PASS", "message": "Connected"}
        except Exception as e:
            report["checks"]["connection"] = {"status": "FAIL", "message": str(e)}

        # Check 2: Entry counts per level
        counts = {}
        for level in MemoryLevel:
            if level == MemoryLevel.STM:
                counts[level.value] = len(self._stm_buffer)
            else:
                cursor = self._conn.execute(
                    "SELECT COUNT(*) as c FROM memory_entries WHERE level = ?", (level.value,)
                )
                counts[level.value] = cursor.fetchone()["c"]
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

    def _enforce_stm_limit(self) -> None:
        config = get_level_config(MemoryLevel.STM)
        if len(self._stm_buffer) > config.max_entries:
            self._stm_buffer = self._stm_buffer[-config.max_entries:]

    def _get_all_entries(self) -> List[Dict]:
        self._ensure_init()
        # STM from buffer
        all_entries = list(self._stm_buffer)
        # Persistent from DB
        rows = self._conn.execute("SELECT * FROM memory_entries").fetchall()
        all_entries.extend([dict(r) for r in rows])
        return all_entries

    def _ensure_init(self):
        if not self._initialized:
            raise RuntimeError("MemoryManager not initialized. Call initialize() first.")
