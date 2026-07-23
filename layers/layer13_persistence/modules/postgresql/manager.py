"""PostgreSQLManager — Enterprise database manager.

Features:
- Connection pool with retry + auto-reconnect
- Repository pattern for type-safe data access
- Health monitoring
- Slow query logging
- Backup/restore
- Performance benchmarks (Insert/Update/Delete latency)
- Transaction recovery verification
- Connection leak detection
- Database statistics (--db-status)
"""
from __future__ import annotations
import os
import json
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from layers.layer13_persistence.modules.postgresql.connection.pool import ConnectionPool, ConnectionConfig
from layers.layer13_persistence.modules.postgresql.migrations.schema import TABLES, get_create_table_sql, get_all_indexes_sql
from layers.layer13_persistence.modules.postgresql.repositories.repositories import (
    ConfigRepository, MemoryRepository, LogRepository,
    PostRepository, AnalyticsRepository, LearningRepository, JobRepository,
)
from layers.layer13_persistence.modules.postgresql.connection.health_checker import DatabaseHealthChecker
from layers.layer13_persistence.modules.postgresql.connection.slow_query_logger import SlowQueryLogger
from layers.layer13_persistence.modules.postgresql.connection.transaction_recovery import TransactionRecovery
from layers.layer13_persistence.modules.postgresql.connection.leak_detector import ConnectionLeakDetector
from layers.layer13_persistence.modules.postgresql.performance.benchmark import PerformanceBenchmark
from layers.layer13_persistence.modules.postgresql.backup.backup_manager import BackupManager


class PostgreSQLManager:
    """Main database manager with full enterprise features."""

    def __init__(self, config: Optional[ConnectionConfig] = None):
        self._config = config or ConnectionConfig.from_env()
        self._pool: Optional[ConnectionPool] = None
        self._initialized = False

        # Repositories
        self.config: Optional[ConfigRepository] = None
        self.memory: Optional[MemoryRepository] = None
        self.logs: Optional[LogRepository] = None
        self.posts: Optional[PostRepository] = None
        self.analytics: Optional[AnalyticsRepository] = None
        self.learning: Optional[LearningRepository] = None
        self.jobs: Optional[JobRepository] = None

        # Enterprise components
        self.health_checker: Optional[DatabaseHealthChecker] = None
        self.slow_query_logger: Optional[SlowQueryLogger] = None
        self.transaction_recovery: Optional[TransactionRecovery] = None
        self.leak_detector: Optional[ConnectionLeakDetector] = None
        self.benchmark: Optional[PerformanceBenchmark] = None
        self.backup_manager: Optional[BackupManager] = None

    def initialize(self) -> bool:
        """Initialize database and all enterprise components."""
        if self._initialized:
            return True

        self._pool = ConnectionPool(self._config)
        pg_available = self._pool.initialize()

        # Initialize repositories
        self.config = ConfigRepository(self._pool)
        self.memory = MemoryRepository(self._pool)
        self.logs = LogRepository(self._pool)
        self.posts = PostRepository(self._pool)
        self.analytics = AnalyticsRepository(self._pool)
        self.learning = LearningRepository(self._pool)
        self.jobs = JobRepository(self._pool)

        # Initialize enterprise components
        self.health_checker = DatabaseHealthChecker(self._pool)
        self.slow_query_logger = SlowQueryLogger()
        self.transaction_recovery = TransactionRecovery(self._pool)
        self.leak_detector = ConnectionLeakDetector()
        self.benchmark = PerformanceBenchmark(self._pool)
        self.backup_manager = BackupManager(self._pool)

        # Create tables
        self._create_tables()

        self._initialized = True
        return pg_available

    def _create_tables(self):
        """Create all tables if they don't exist."""
        for table in TABLES:
            cols = ", ".join(table["columns"])
            sql = f"CREATE TABLE IF NOT EXISTS {table['name']} ({cols})"
            try:
                self._pool.execute(sql)
            except Exception:
                pass
        for idx_sql in get_all_indexes_sql():
            try:
                self._pool.execute(idx_sql)
            except Exception:
                pass

    def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check."""
        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "initialized": self._initialized,
            "pool": self._pool.get_pool_metrics() if self._pool else None,
            "tables": {},
            "overall": "PASS",
        }
        if self._pool:
            tables = self._pool.get_tables()
            for table in TABLES:
                name = table["name"]
                exists = name in tables
                count = self._pool.count(name) if exists else 0
                report["tables"][name] = {"exists": exists, "row_count": count}
        missing = [t["name"] for t in TABLES if not report["tables"].get(t["name"], {}).get("exists")]
        if missing:
            report["overall"] = "FAIL"
            report["missing_tables"] = missing
        return report

    def get_db_status(self) -> Dict[str, Any]:
        """Get comprehensive database status — for --db-status command."""
        pool_metrics = self._pool.get_pool_metrics() if self._pool else {}
        health = self.health_checker.check() if self.health_checker else {}
        slow_stats = self.slow_query_logger.get_stats() if self.slow_query_logger else {}
        leak_stats = self.leak_detector.get_stats() if self.leak_detector else {}

        # Table stats
        tables = {}
        total_rows = 0
        if self._pool:
            for table in TABLES:
                name = table["name"]
                count = self._pool.count(name)
                tables[name] = count
                total_rows += count

        # Overall health
        pool_healthy = pool_metrics.get("healthy", False)
        no_leaks = leak_stats.get("total_leaks_detected", 0) == 0
        slow_pct = slow_stats.get("slow_pct", 0)
        overall = "Healthy" if pool_healthy and no_leaks and slow_pct < 10 else "Degraded"

        return {
            "overall": overall,
            "connections": {
                "active": pool_metrics.get("active_connections", 0),
                "idle": pool_metrics.get("idle_connections", 0),
                "max_pool_size": pool_metrics.get("config", {}).get("max_connections", 0),
                "total_queries": pool_metrics.get("total_queries", 0),
                "failed_queries": pool_metrics.get("failed_queries", 0),
                "total_retries": pool_metrics.get("total_retries", 0),
            },
            "latency": {
                "avg_ms": pool_metrics.get("latency", {}).get("avg_ms", 0),
                "p95_ms": pool_metrics.get("latency", {}).get("p95_ms", 0),
                "p99_ms": pool_metrics.get("latency", {}).get("p99_ms", 0),
            },
            "slow_queries": {
                "total": slow_stats.get("slow_count", 0),
                "slow_pct": slow_stats.get("slow_pct", 0),
                "threshold_ms": slow_stats.get("threshold_ms", 500),
            },
            "leak_detection": {
                "active_connections": leak_stats.get("currently_active", 0),
                "total_leaks_detected": leak_stats.get("total_leaks_detected", 0),
                "total_acquired": leak_stats.get("total_acquired", 0),
                "total_released": leak_stats.get("total_released", 0),
            },
            "tables": tables,
            "total_rows": total_rows,
            "postgresql_available": pool_metrics.get("postgresql_available", False),
            "initialized": self._initialized,
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        stats = {"initialized": self._initialized, "tables": {}, "total_rows": 0}
        if self._pool:
            for table in TABLES:
                name = table["name"]
                count = self._pool.count(name)
                stats["tables"][name] = count
                stats["total_rows"] += count
        return stats

    def run_benchmark(self) -> Dict[str, Any]:
        """Run performance benchmarks."""
        if self.benchmark:
            return self.benchmark.run_all()
        return {"error": "benchmark not initialized"}

    def backup(self, name: Optional[str] = None) -> Dict[str, Any]:
        """Create database backup."""
        if self.backup_manager:
            return self.backup_manager.backup(name)
        return {"error": "backup manager not initialized"}

    def restore(self, filepath: str) -> Dict[str, Any]:
        """Restore from backup."""
        if self.backup_manager:
            return self.backup_manager.restore(filepath)
        return {"error": "backup manager not initialized"}

    def get_slow_queries(self) -> List[Dict[str, Any]]:
        """Get slow query log."""
        if self.slow_query_logger:
            return self.slow_query_logger.get_slow_queries()
        return []

    def get_pool_metrics(self) -> Dict[str, Any]:
        """Get connection pool metrics."""
        if self._pool:
            return self._pool.get_pool_metrics()
        return {}

    def run_transaction_recovery(self) -> Dict[str, Any]:
        """Run all transaction recovery tests."""
        if self.transaction_recovery:
            return self.transaction_recovery.run_all()
        return {"error": "transaction recovery not initialized"}

    def check_leaks(self) -> List[Dict[str, Any]]:
        """Check for connection leaks."""
        if self.leak_detector:
            return self.leak_detector.check_leaks()
        return []

    def close(self):
        """Close all connections and stop monitors."""
        if self.health_checker:
            self.health_checker.stop_monitoring()
        if self.leak_detector:
            self.leak_detector.stop_monitoring()
        if self._pool:
            self._pool.close()
        self._initialized = False


# Singleton
_db_instance: Optional[PostgreSQLManager] = None


def get_database(config: Optional[ConnectionConfig] = None) -> PostgreSQLManager:
    """Get or create database singleton."""
    global _db_instance
    if _db_instance is None:
        _db_instance = PostgreSQLManager(config)
        _db_instance.initialize()
    return _db_instance
