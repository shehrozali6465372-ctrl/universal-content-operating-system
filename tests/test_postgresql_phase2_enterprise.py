"""Tests for PostgreSQL Phase 2 Enterprise Features.

Covers:
- Connection Leak Detection
- Enhanced Transaction Recovery (BEGIN→INSERT→UPDATE→CRASH→ROLLBACK)
- Slow Query Logger
- Health Checker
- Pool Metrics
- Performance Benchmark (Insert/Update/Delete latency)
- Repository Benchmark (Insert/Update/Delete breakdown)
- PostgreSQLManager get_db_status
"""
from __future__ import annotations
import os
import sys
import time
import threading
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# SQLite-compatible table creation for tests
_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS agent_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT UNIQUE NOT NULL,
    value TEXT NOT NULL,
    category TEXT DEFAULT 'general'
)
"""


def _ensure_table(pool):
    """Create agent_config table if it doesn't exist."""
    try:
        pool.execute(_CREATE_TABLE_SQL)
    except Exception:
        pass



# ─── Connection Leak Detector Tests ──────────────────────────────

class TestConnectionLeakDetector:
    def setup_method(self):
        from layers.layer13_persistence.modules.postgresql.connection.leak_detector import ConnectionLeakDetector
        self.detector = ConnectionLeakDetector(leak_timeout_seconds=0.1, check_interval_seconds=0.05)

    def teardown_method(self):
        self.detector.stop_monitoring()
        self.detector.reset()

    def test_acquire_returns_tracking_id(self):
        conn_id = self.detector.acquire()
        assert conn_id is not None
        assert conn_id.startswith("conn_")

    def test_release_tracked_connection(self):
        conn_id = self.detector.acquire()
        released = self.detector.release(conn_id)
        assert released is True

    def test_release_untracked_returns_false(self):
        released = self.detector.release("nonexistent")
        assert released is False

    def test_double_release_returns_false(self):
        conn_id = self.detector.acquire()
        self.detector.release(conn_id)
        released = self.detector.release(conn_id)
        assert released is False

    def test_leak_detection_finds_old_connections(self):
        c1 = self.detector.acquire()
        c2 = self.detector.acquire()
        self.detector.release(c1)  # Release one
        time.sleep(0.2)  # Wait for timeout
        leaks = self.detector.check_leaks()
        assert len(leaks) == 1
        assert leaks[0]["connection_id"] == c2

    def test_no_leaks_when_all_released(self):
        c1 = self.detector.acquire()
        c2 = self.detector.acquire()
        self.detector.release(c1)
        self.detector.release(c2)
        time.sleep(0.2)
        leaks = self.detector.check_leaks()
        assert len(leaks) == 0

    def test_stats_tracking(self):
        c1 = self.detector.acquire()
        c2 = self.detector.acquire()
        self.detector.release(c1)
        time.sleep(0.2)
        self.detector.check_leaks()
        stats = self.detector.get_stats()
        assert stats["total_acquired"] == 2
        assert stats["total_released"] == 1
        assert stats["currently_active"] == 1
        assert stats["total_leaks_detected"] == 1

    def test_active_connections_list(self):
        c1 = self.detector.acquire()
        c2 = self.detector.acquire()
        self.detector.release(c1)
        active = self.detector.get_active_connections()
        assert len(active) == 1
        assert active[0]["connection_id"] == c2

    def test_monitoring_start_stop(self):
        self.detector.start_monitoring()
        assert self.detector._monitoring is True
        assert self.detector._monitor_thread is not None
        self.detector.stop_monitoring()
        assert self.detector._monitoring is False

    def test_monitoring_detects_leaks(self):
        self.detector.start_monitoring()
        self.detector.acquire()  # Don't release
        time.sleep(0.3)  # Wait for monitor cycle
        stats = self.detector.get_stats()
        assert stats["total_leaks_detected"] >= 1

    def test_reset_clears_state(self):
        self.detector.acquire()
        self.detector.reset()
        stats = self.detector.get_stats()
        assert stats["total_acquired"] == 0
        assert stats["total_released"] == 0


# ─── Transaction Recovery Tests ──────────────────────────────────

class TestTransactionRecovery:
    def setup_method(self):
        from layers.layer13_persistence.modules.postgresql.connection.pool import ConnectionPool
        self.pool = ConnectionPool()
        self.pool.initialize()
        _ensure_table(self.pool)

    def teardown_method(self):
        self.pool.close()

    def test_rollback(self):
        from layers.layer13_persistence.modules.postgresql.connection.transaction_recovery import TransactionRecovery
        recovery = TransactionRecovery(self.pool)
        result = recovery.test_rollback()
        assert result["passed"] is True

    def test_crash_recovery(self):
        from layers.layer13_persistence.modules.postgresql.connection.transaction_recovery import TransactionRecovery
        recovery = TransactionRecovery(self.pool)
        result = recovery.test_crash_recovery()
        assert result["passed"] is True

    def test_commit_persistence(self):
        from layers.layer13_persistence.modules.postgresql.connection.transaction_recovery import TransactionRecovery
        recovery = TransactionRecovery(self.pool)
        result = recovery.test_commit_persistence()
        assert result["passed"] is True

    def test_insert_update_commit(self):
        from layers.layer13_persistence.modules.postgresql.connection.transaction_recovery import TransactionRecovery
        recovery = TransactionRecovery(self.pool)
        result = recovery.test_insert_update_commit()
        assert result["passed"] is True

    def test_concurrent_rollback(self):
        from layers.layer13_persistence.modules.postgresql.connection.transaction_recovery import TransactionRecovery
        recovery = TransactionRecovery(self.pool)
        result = recovery.test_concurrent_rollback()
        assert result["passed"] is True

    def test_run_all(self):
        from layers.layer13_persistence.modules.postgresql.connection.transaction_recovery import TransactionRecovery
        recovery = TransactionRecovery(self.pool)
        result = recovery.run_all()
        assert result["total"] == 5
        assert result["passed"] >= 4

    def test_journal_tracking(self):
        from layers.layer13_persistence.modules.postgresql.connection.transaction_recovery import TransactionRecovery
        recovery = TransactionRecovery(self.pool)
        recovery.test_rollback()
        journal = recovery.get_journal()
        assert len(journal) >= 1
        assert journal[-1]["action"] == "rollback"


# ─── Slow Query Logger Tests ─────────────────────────────────────

class TestSlowQueryLogger:
    def setup_method(self):
        from layers.layer13_persistence.modules.postgresql.connection.slow_query_logger import SlowQueryLogger
        self.logger = SlowQueryLogger(threshold_ms=50.0)

    def test_fast_query_not_logged(self):
        self.logger.record("SELECT 1", 5.0)
        stats = self.logger.get_stats()
        assert stats["total_queries"] == 1
        assert stats["slow_count"] == 0

    def test_slow_query_logged(self):
        self.logger.record("SELECT * FROM big_table", 100.0)
        slow = self.logger.get_slow_queries()
        assert len(slow) == 1

    def test_latency_stats(self):
        for i in range(100):
            self.logger.record(f"SELECT {i}", float(i))
        stats = self.logger.get_stats()
        assert stats["total_queries"] == 100
        assert stats["slow_count"] >= 50  # latencies >= 50
        assert stats["avg_latency_ms"] > 0
        assert stats["p95_ms"] > 0
        assert stats["p99_ms"] > 0

    def test_reset(self):
        self.logger.record("SELECT 1", 100.0)
        self.logger.reset()
        stats = self.logger.get_stats()
        assert stats["total_queries"] == 0

    def test_max_slow_limit(self):
        for i in range(1100):
            self.logger.record(f"SELECT {i}", 200.0)
        slow = self.logger.get_slow_queries()
        assert len(slow) <= 1000


# ─── Health Checker Tests ────────────────────────────────────────

class TestHealthChecker:
    def setup_method(self):
        from layers.layer13_persistence.modules.postgresql.connection.pool import ConnectionPool
        from layers.layer13_persistence.modules.postgresql.connection.health_checker import DatabaseHealthChecker
        self.pool = ConnectionPool()
        self.pool.initialize()
        _ensure_table(self.pool)
        self.checker = DatabaseHealthChecker(self.pool)

    def teardown_method(self):
        self.pool.close()

    def test_check_returns_healthy(self):
        result = self.checker.check()
        assert result["connection_alive"] is True
        assert result["status"] == "healthy"

    def test_check_has_response_time(self):
        result = self.checker.check()
        assert result["response_time_ms"] > 0

    def test_check_has_pool_metrics(self):
        result = self.checker.check()
        assert "pool_metrics" in result

    def test_history_tracking(self):
        self.checker.check()
        self.checker.check()
        history = self.checker.get_history(limit=10)
        assert len(history) == 2

    def test_summary(self):
        self.checker.check()
        summary = self.checker.get_summary()
        assert summary["total_checks"] == 1
        assert summary["alive_count"] == 1

    def test_monitoring_start_stop(self):
        self.checker.start_monitoring()
        time.sleep(0.5)
        self.checker.stop_monitoring()
        summary = self.checker.get_summary()
        assert summary["total_checks"] >= 1


# ─── Pool Metrics Tests ──────────────────────────────────────────

class TestPoolMetrics:
    def setup_method(self):
        from layers.layer13_persistence.modules.postgresql.connection.pool import ConnectionPool
        self.pool = ConnectionPool()
        self.pool.initialize()
        _ensure_table(self.pool)

    def teardown_method(self):
        self.pool.close()

    def test_has_required_keys(self):
        metrics = self.pool.get_pool_metrics()
        required = [
            "postgresql_available", "initialized", "healthy",
            "active_connections", "idle_connections",
            "total_queries", "failed_queries", "total_retries",
            "latency",
        ]
        for key in required:
            assert key in metrics, f"Missing key: {key}"

    def test_latency_has_percentiles(self):
        metrics = self.pool.get_pool_metrics()
        latency = metrics["latency"]
        assert "avg_ms" in latency
        assert "p95_ms" in latency
        assert "p99_ms" in latency

    def test_query_count_increments(self):
        before = self.pool.get_pool_metrics()["total_queries"]
        self.pool.query_one("SELECT 1")
        after = self.pool.get_pool_metrics()["total_queries"]
        assert after > before

    def test_config_in_metrics(self):
        metrics = self.pool.get_pool_metrics()
        config = metrics["config"]
        assert "host" in config
        assert "port" in config
        assert "database" in config


# ─── Performance Benchmark Tests ─────────────────────────────────

class TestPerformanceBenchmark:
    def setup_method(self):
        from layers.layer13_persistence.modules.postgresql.connection.pool import ConnectionPool
        from layers.layer13_persistence.modules.postgresql.performance.benchmark import PerformanceBenchmark
        self.pool = ConnectionPool()
        self.pool.initialize()
        _ensure_table(self.pool)
        self.bench = PerformanceBenchmark(self.pool)

    def teardown_method(self):
        self.pool.close()

    def test_insert_benchmark(self):
        result = self.bench.run_insert_benchmark(count=50)
        assert result["passed"] is True
        assert result["count"] == 50
        assert "latency" in result

    def test_read_benchmark(self):
        result = self.bench.run_read_benchmark(count=100)
        assert result["passed"] is True
        assert "latency" in result

    def test_update_benchmark(self):
        result = self.bench.run_update_benchmark(count=50)
        assert result["passed"] is True
        assert "latency" in result

    def test_delete_benchmark(self):
        result = self.bench.run_delete_benchmark(count=50)
        assert result["passed"] is True
        assert "latency" in result

    def test_concurrent_benchmark(self):
        result = self.bench.run_concurrent_benchmark(threads=3, ops_per_thread=20)
        assert result["passed"] is True

    def test_repository_benchmark(self):
        result = self.bench.run_repository_benchmark()
        assert result["passed"] is True
        assert "config_repo" in result["results"]

    def test_repository_benchmark_has_crud_latency(self):
        result = self.bench.run_repository_benchmark()
        config = result["results"]["config_repo"]
        assert "insert" in config
        assert "read" in config
        assert "update" in config
        assert "delete" in config

    def test_run_all(self):
        result = self.bench.run_all()
        assert "results" in result
        assert result["total_count"] == 6


# ─── PostgreSQLManager get_db_status Tests ───────────────────────

class TestPostgreSQLManagerDbStatus:
    def setup_method(self):
        from layers.layer13_persistence.modules.postgresql.manager import PostgreSQLManager, ConnectionConfig
        self.manager = PostgreSQLManager(ConnectionConfig())
        self.manager.initialize()
        _ensure_table(self.manager._pool)

    def teardown_method(self):
        self.manager.close()

    def test_db_status_has_overall(self):
        status = self.manager.get_db_status()
        assert "overall" in status
        assert status["overall"] in ("Healthy", "Degraded")

    def test_db_status_has_connections(self):
        status = self.manager.get_db_status()
        conn = status["connections"]
        assert "active" in conn
        assert "idle" in conn
        assert "max_pool_size" in conn
        assert "total_queries" in conn
        assert "failed_queries" in conn

    def test_db_status_has_latency(self):
        status = self.manager.get_db_status()
        lat = status["latency"]
        assert "avg_ms" in lat
        assert "p95_ms" in lat
        assert "p99_ms" in lat

    def test_db_status_has_slow_queries(self):
        status = self.manager.get_db_status()
        slow = status["slow_queries"]
        assert "total" in slow
        assert "slow_pct" in slow

    def test_db_status_has_leak_detection(self):
        status = self.manager.get_db_status()
        leak = status["leak_detection"]
        assert "active_connections" in leak
        assert "total_leaks_detected" in leak

    def test_db_status_has_tables(self):
        status = self.manager.get_db_status()
        assert "tables" in status
        assert "total_rows" in status

    def test_run_transaction_recovery(self):
        result = self.manager.run_transaction_recovery()
        assert result["total"] == 5

    def test_check_leaks(self):
        leaks = self.manager.check_leaks()
        assert isinstance(leaks, list)


# ─── Integration Test ────────────────────────────────────────────

class TestPhase2EnterpriseIntegration:
    def setup_method(self):
        from layers.layer13_persistence.modules.postgresql.manager import PostgreSQLManager, ConnectionConfig
        self.manager = PostgreSQLManager(ConnectionConfig())
        self.manager.initialize()
        _ensure_table(self.manager._pool)

    def teardown_method(self):
        self.manager.close()

    def test_full_enterprise_stack(self):
        """Test that all enterprise components work together."""
        # Leak detector
        detector = self.manager.leak_detector
        c1 = detector.acquire()
        detector.release(c1)

        # Slow query logger
        logger = self.manager.slow_query_logger
        logger.record("SELECT 1", 5.0)

        # Transaction recovery
        recovery = self.manager.transaction_recovery
        result = recovery.test_rollback()
        assert result["passed"] is True

        # Health checker
        health = self.manager.health_checker.check()
        assert health["connection_alive"] is True

        # Pool metrics
        metrics = self.manager.get_pool_metrics()
        assert "latency" in metrics

        # DB status
        status = self.manager.get_db_status()
        assert status["overall"] in ("Healthy", "Degraded")

    def test_db_status_matches_components(self):
        """Verify db_status aggregates from individual components."""
        # Run a query to generate metrics
        self.manager._pool.query_one("SELECT 1")
        status = self.manager.get_db_status()
        assert status["connections"]["total_queries"] >= 1
