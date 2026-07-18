"""Tests for Layer 13 — Enterprise Persistence Platform."""
from __future__ import annotations
import pytest

from layers.layer13_persistence.modules.persistence_kernel.persistence_kernel import PersistenceKernel
from layers.layer13_persistence.modules.persistence_kernel.persistence_manager import PersistenceManager
from layers.layer13_persistence.modules.persistence_kernel.persistence_lifecycle import PersistenceLifecycle
from layers.layer13_persistence.modules.persistence_kernel.persistence_context import PersistenceContext
from layers.layer13_persistence.modules.persistence_kernel.persistence_configuration import PersistenceConfiguration
from layers.layer13_persistence.modules.persistence_kernel.persistence_bootstrap import PersistenceBootstrap
from layers.layer13_persistence.modules.persistence_kernel.persistence_health import PersistenceHealth
from layers.layer13_persistence.modules.persistence_kernel.persistence_metrics import PersistenceMetrics
from layers.layer13_persistence.modules.persistence_kernel.persistence_events import PersistenceEvents
from layers.layer13_persistence.modules.persistence_kernel.persistence_report import PersistenceReport
from layers.layer13_persistence.modules.persistence_kernel.persistence_version import PersistenceVersion
from layers.layer13_persistence.modules.persistence_kernel.exceptions import (
    PersistenceError, StorageError, ConnectionError, TransactionError,
    QueryError, MigrationError, BackupError, RestoreError, CacheError,
    ValidationError, ConfigurationError, HealthCheckError, VersionError
)


# ═══════════════════════════════════════════════════════════════════════
# PersistenceKernel
# ═══════════════════════════════════════════════════════════════════════

class TestPersistenceKernel:
    def setup_method(self):
        self.k = PersistenceKernel()

    def test_start_stop(self):
        assert self.k.start() is True
        assert self.k.is_running() is True
        assert self.k.stop() is True
        assert self.k.is_running() is False

    def test_double_start(self):
        self.k.start()
        assert self.k.start() is True

    def test_double_stop(self):
        self.k.stop()
        assert self.k.stop() is True

    def test_register_store(self):
        mock_store = {"type": "memory"}
        assert self.k.register_store("mem", mock_store) is True
        assert self.k.get_store("mem") is mock_store

    def test_unregister_store(self):
        self.k.register_store("mem", {"type": "memory"})
        assert self.k.unregister_store("mem") is True
        assert self.k.unregister_store("mem") is False

    def test_get_all_stores(self):
        self.k.register_store("a", {"a": 1})
        self.k.register_store("b", {"b": 2})
        stores = self.k.get_all_stores()
        assert len(stores) == 2

    def test_uptime(self):
        self.k.start()
        assert self.k.get_uptime() >= 0

    def test_health(self):
        h = self.k.get_health()
        assert isinstance(h, dict)

    def test_metrics(self):
        m = self.k.get_metrics()
        assert isinstance(m, dict)

    def test_events(self):
        self.k.start()
        ev = self.k.get_events()
        assert len(ev) >= 1

    def test_version(self):
        v = self.k.get_version()
        assert "current_version" in v

    def test_status(self):
        s = self.k.status()
        assert "running" in s
        assert "stores" in s


# ═══════════════════════════════════════════════════════════════════════
# PersistenceManager
# ═══════════════════════════════════════════════════════════════════════

class TestPersistenceManager:
    def setup_method(self):
        self.pm = PersistenceManager()

    def test_initialize_shutdown(self):
        assert self.pm.initialize() is True
        assert self.pm.is_initialized() is True
        assert self.pm.shutdown() is True
        assert self.pm.is_initialized() is False

    def test_route(self):
        self.pm.route("user_data", "postgresql")
        assert self.pm.get_route("user_data") == "postgresql"

    def test_get_route_default(self):
        assert self.pm.get_route("unknown") == "default"

    def test_all_routes(self):
        self.pm.route("a", "db1")
        self.pm.route("b", "db2")
        assert len(self.pm.get_all_routes()) == 2

    def test_status(self):
        s = self.pm.status()
        assert "initialized" in s


# ═══════════════════════════════════════════════════════════════════════
# PersistenceLifecycle
# ═══════════════════════════════════════════════════════════════════════

class TestPersistenceLifecycle:
    def setup_method(self):
        self.lc = PersistenceLifecycle()

    def test_register(self):
        self.lc.register("mem", {})
        assert self.lc.get_state("mem") == "registered"

    def test_initialize_store(self):
        self.lc.register("mem", {})
        assert self.lc.initialize_store("mem") is True
        assert self.lc.get_state("mem") == "initialized"

    def test_close_store(self):
        self.lc.register("mem", {})
        self.lc.close_store("mem")
        assert self.lc.get_state("mem") == "closed"

    def test_events(self):
        self.lc.register("mem", {})
        self.lc.initialize_store("mem")
        ev = self.lc.get_events("mem")
        assert len(ev) >= 1

    def test_on_hook(self):
        received = []
        self.lc.on("initialized", lambda e: received.append(e))
        self.lc.register("mem", {})
        self.lc.initialize_store("mem")
        assert len(received) == 1

    def test_all_states(self):
        self.lc.register("a", {})
        self.lc.register("b", {})
        states = self.lc.get_all_states()
        assert len(states) == 2

    def test_to_dict(self):
        self.lc.register("mem", {})
        d = self.lc.to_dict()
        assert d["stores"] == 1


# ═══════════════════════════════════════════════════════════════════════
# PersistenceContext
# ═══════════════════════════════════════════════════════════════════════

class TestPersistenceContext:
    def test_create(self):
        ctx = PersistenceContext(user_id="u1", session_id="s1", operation="store")
        assert ctx.user_id == "u1"

    def test_add_trace(self):
        ctx = PersistenceContext()
        ctx.add_trace("step1", {"detail": "test"})
        assert len(ctx.trace) == 1

    def test_set_transaction(self):
        ctx = PersistenceContext()
        ctx.set_transaction("tx_123")
        assert ctx.transaction_id == "tx_123"

    def test_elapsed(self):
        ctx = PersistenceContext()
        assert ctx.elapsed_ms() >= 0

    def test_to_dict(self):
        ctx = PersistenceContext()
        d = ctx.to_dict()
        assert "context_id" in d


# ═══════════════════════════════════════════════════════════════════════
# PersistenceConfiguration
# ═══════════════════════════════════════════════════════════════════════

class TestPersistenceConfiguration:
    def test_defaults(self):
        cfg = PersistenceConfiguration()
        assert cfg.pool_size == 20
        assert cfg.enable_cache is True

    def test_to_dict(self):
        d = PersistenceConfiguration().to_dict()
        assert "database_url" in d

    def test_from_dict(self):
        cfg = PersistenceConfiguration.from_dict({"pool_size": 50})
        assert cfg.pool_size == 50


# ═══════════════════════════════════════════════════════════════════════
# PersistenceBootstrap
# ═══════════════════════════════════════════════════════════════════════

class TestPersistenceBootstrap:
    def test_bootstrap(self):
        bs = PersistenceBootstrap()
        assert bs.bootstrap() is True
        assert bs.is_bootstrapped() is True

    def test_shutdown(self):
        bs = PersistenceBootstrap()
        bs.bootstrap()
        assert bs.shutdown() is True
        assert bs.is_bootstrapped() is False

    def test_register_store(self):
        bs = PersistenceBootstrap()
        bs.register_store("mem", {"data": 1})
        assert bs.get_kernel().get_store("mem") is not None

    def test_status(self):
        bs = PersistenceBootstrap()
        bs.bootstrap()
        s = bs.status()
        assert "bootstrapped" in s


# ═══════════════════════════════════════════════════════════════════════
# PersistenceHealth
# ═══════════════════════════════════════════════════════════════════════

class TestPersistenceHealth:
    def test_check_store(self):
        h = PersistenceHealth()
        result = h.check_store("mem", True, 1.5)
        assert result["healthy"] is True

    def test_is_healthy(self):
        h = PersistenceHealth()
        h.check_store("a", True)
        h.check_store("b", True)
        assert h.is_healthy() is True

    def test_degraded(self):
        h = PersistenceHealth()
        h.check_store("a", True)
        h.check_store("b", False)
        assert h.is_healthy() is False

    def test_mark_started_stopped(self):
        h = PersistenceHealth()
        h.mark_started()
        assert h.is_healthy() is True
        h.mark_stopped()

    def test_get_store_health(self):
        h = PersistenceHealth()
        h.check_store("mem", True, 2.0)
        s = h.get_store_health("mem")
        assert s["healthy"] is True


# ═══════════════════════════════════════════════════════════════════════
# PersistenceMetrics
# ═══════════════════════════════════════════════════════════════════════

class TestPersistenceMetrics:
    def test_record_store(self):
        m = PersistenceMetrics()
        m.record_store_registered("mem")
        assert m._stores_registered == 1

    def test_record_operation(self):
        m = PersistenceMetrics()
        m.record_operation("store", True)
        assert m._total_operations == 1

    def test_record_error(self):
        m = PersistenceMetrics()
        m.record_operation("store", False)
        assert m.get_error_rate() == 1.0

    def test_record_count(self):
        m = PersistenceMetrics()
        m.record_count("mem", 100)
        assert m.get_total() == 100

    def test_to_dict(self):
        m = PersistenceMetrics()
        d = m.to_dict()
        assert "total_operations" in d


# ═══════════════════════════════════════════════════════════════════════
# PersistenceEvents
# ═══════════════════════════════════════════════════════════════════════

class TestPersistenceEvents:
    def test_publish_subscribe(self):
        ev = PersistenceEvents()
        received = []
        ev.subscribe("test", lambda e: received.append(e))
        ev.publish("test", {"msg": "hi"})
        assert len(received) == 1

    def test_wildcard(self):
        ev = PersistenceEvents()
        received = []
        ev.subscribe("*", lambda e: received.append(e))
        ev.publish("anything")
        assert len(received) == 1

    def test_get_recent(self):
        ev = PersistenceEvents()
        ev.publish("a", {})
        ev.publish("b", {})
        recent = ev.get_recent(10)
        assert len(recent) == 2

    def test_get_by_type(self):
        ev = PersistenceEvents()
        ev.publish("a", {})
        ev.publish("b", {})
        ev.publish("a", {})
        assert len(ev.get_by_type("a")) == 2

    def test_clear(self):
        ev = PersistenceEvents()
        ev.publish("a", {})
        ev.clear()
        assert ev.get_stats()["total"] == 0

    def test_stats(self):
        ev = PersistenceEvents()
        ev.publish("a", {})
        ev.publish("a", {})
        ev.publish("b", {})
        s = ev.get_stats()
        assert s["total"] == 3


# ═══════════════════════════════════════════════════════════════════════
# PersistenceReport
# ═══════════════════════════════════════════════════════════════════════

class TestPersistenceReport:
    def test_generate(self):
        rp = PersistenceReport()
        report = rp.generate({"total_operations": 100}, {"status": "healthy"},
                              {"mem": {"type": "memory"}})
        assert "summary" in report

    def test_history(self):
        rp = PersistenceReport()
        rp.generate({}, {}, {})
        h = rp.get_history()
        assert len(h) == 1


# ═══════════════════════════════════════════════════════════════════════
# PersistenceVersion
# ═══════════════════════════════════════════════════════════════════════

class TestPersistenceVersion:
    def test_current(self):
        v = PersistenceVersion()
        assert v.get_current() == "1.0.0"

    def test_upgrade(self):
        v = PersistenceVersion()
        assert v.upgrade("2.0.0", "Added new tables") is True
        assert v.get_current() == "2.0.0"

    def test_history(self):
        v = PersistenceVersion()
        v.upgrade("2.0.0")
        h = v.get_history()
        assert len(h) == 2

    def test_migrations(self):
        v = PersistenceVersion()
        v.register_migration("1.0.0", "2.0.0", "Upgrade")
        assert len(v.get_migrations()) == 1


# ═══════════════════════════════════════════════════════════════════════
# Exceptions
# ═══════════════════════════════════════════════════════════════════════

class TestPersistenceExceptions:
    def test_hierarchy(self):
        assert issubclass(PersistenceError, Exception)
        assert issubclass(StorageError, PersistenceError)
        assert issubclass(ConnectionError, PersistenceError)
        assert issubclass(TransactionError, PersistenceError)
        assert issubclass(QueryError, PersistenceError)
        assert issubclass(MigrationError, PersistenceError)
        assert issubclass(BackupError, PersistenceError)
        assert issubclass(RestoreError, PersistenceError)
        assert issubclass(CacheError, PersistenceError)
        assert issubclass(ValidationError, PersistenceError)
        assert issubclass(ConfigurationError, PersistenceError)
        assert issubclass(HealthCheckError, PersistenceError)
        assert issubclass(VersionError, PersistenceError)

    def test_raise(self):
        with pytest.raises(StorageError):
            raise StorageError("test")

    def test_catch_base(self):
        with pytest.raises(PersistenceError):
            raise ConnectionError("test")


# ═══════════════════════════════════════════════════════════════════════
# MODULE 2: SQL Database Platform
# ═══════════════════════════════════════════════════════════════════════

from layers.layer13_persistence.modules.sql_database_platform.connection_manager import ConnectionManager
from layers.layer13_persistence.modules.sql_database_platform.pool_manager import PoolManager
from layers.layer13_persistence.modules.sql_database_platform.transaction_manager import TransactionManager
from layers.layer13_persistence.modules.sql_database_platform.query_executor import QueryExecutor, QueryResult
from layers.layer13_persistence.modules.sql_database_platform.prepared_statement import PreparedStatementManager
from layers.layer13_persistence.modules.sql_database_platform.orm_bridge import ORMBridge, ORMModel
from layers.layer13_persistence.modules.sql_database_platform.schema_manager import SchemaManager, TableSchema
from layers.layer13_persistence.modules.sql_database_platform.migration_engine import MigrationEngine, Migration
from layers.layer13_persistence.modules.sql_database_platform.index_manager import IndexManager, DatabaseIndex
from layers.layer13_persistence.modules.sql_database_platform.partition_manager import PartitionManager, Partition
from layers.layer13_persistence.modules.sql_database_platform.replication_manager import ReplicationManager, ReplicaNode
from layers.layer13_persistence.modules.sql_database_platform.backup_manager import BackupManager
from layers.layer13_persistence.modules.sql_database_platform.restore_manager import RestoreManager
from layers.layer13_persistence.modules.sql_database_platform.optimizer import QueryOptimizer
from layers.layer13_persistence.modules.sql_database_platform.query_analyzer import QueryAnalyzer
from layers.layer13_persistence.modules.sql_database_platform.deadlock_detector import DeadlockDetector, LockRequest
from layers.layer13_persistence.modules.sql_database_platform.lock_manager import LockManager
from layers.layer13_persistence.modules.sql_database_platform.sql_metrics import SQLMetrics
from layers.layer13_persistence.modules.sql_database_platform.sql_health import SQLHealth
from layers.layer13_persistence.modules.sql_database_platform.sql_report import SQLReport


class TestConnectionManager:
    def setup_method(self):
        self.cm = ConnectionManager()

    def test_configure(self):
        self.cm.configure("testdb", "localhost", 5432, "admin")
        assert self.cm._config["database"] == "testdb"

    def test_connect(self):
        conn = self.cm.connect("main")
        assert conn.is_active
        assert conn.database == "default"

    def test_disconnect(self):
        self.cm.connect("main")
        assert self.cm.disconnect("main") is True
        assert self.cm.disconnect("main") is False

    def test_disconnect_all(self):
        self.cm.connect("a")
        self.cm.connect("b")
        assert self.cm.disconnect_all() == 2

    def test_get_active(self):
        self.cm.connect("a")
        active = self.cm.get_active()
        assert len(active) >= 1

    def test_is_connected(self):
        self.cm.connect("main")
        assert self.cm.is_connected("main") is True
        assert self.cm.is_connected("other") is False

    def test_to_dict(self):
        d = self.cm.to_dict()
        assert "connections" in d


class TestPoolManager:
    def setup_method(self):
        self.pm = PoolManager(pool_size=5, max_overflow=2)

    def test_initialize(self):
        assert self.pm.initialize() is True

    def test_acquire(self):
        self.pm.initialize()
        entry = self.pm.acquire()
        assert entry is not None
        assert entry.in_use is True

    def test_release(self):
        self.pm.initialize()
        entry = self.pm.acquire()
        assert self.pm.release(entry) is True
        assert entry.in_use is False

    def test_overflow(self):
        self.pm.initialize()
        entries = []
        for _ in range(7):
            e = self.pm.acquire()
            if e:
                entries.append(e)
        assert len(entries) >= 5

    def test_exhausted(self):
        pm = PoolManager(pool_size=1, max_overflow=0)
        pm.initialize()
        pm.acquire()
        assert pm.acquire() is None

    def test_stats(self):
        self.pm.initialize()
        s = self.pm.get_stats()
        assert s["pool_size"] == 5

    def test_close_all(self):
        self.pm.initialize()
        count = self.pm.close_all()
        assert count >= 5


class TestTransactionManager:
    def setup_method(self):
        self.tm = TransactionManager()

    def test_begin(self):
        tx = self.tm.begin()
        assert tx.status == "active"

    def test_commit(self):
        tx = self.tm.begin()
        assert self.tm.commit(tx.tx_id) is True
        assert len(self.tm.get_completed()) == 1

    def test_rollback(self):
        tx = self.tm.begin()
        assert self.tm.rollback(tx.tx_id) is True
        assert tx.rolled_back is True

    def test_execute_in_transaction(self):
        result = self.tm.execute_in_transaction(lambda: "ok")
        assert result == "ok"

    def test_get_active(self):
        self.tm.begin()
        self.tm.begin()
        assert len(self.tm.get_active()) == 2

    def test_stats(self):
        self.tm.begin()
        s = self.tm.stats()
        assert s["active"] == 1


class TestQueryExecutor:
    def setup_method(self):
        self.qe = QueryExecutor()

    def test_execute(self):
        result = self.qe.execute("SELECT 1")
        assert isinstance(result, QueryResult)

    def test_fetch_one(self):
        result = self.qe.fetch_one("SELECT 1")
        assert result is None or isinstance(result, dict)

    def test_fetch_all(self):
        results = self.qe.fetch_all("SELECT * FROM users")
        assert isinstance(results, list)

    def test_execute_many(self):
        result = self.qe.execute_many("INSERT INTO t VALUES (?)", [{"a": 1}, {"a": 2}])
        assert result.affected_rows == 2

    def test_stats(self):
        self.qe.execute("SELECT 1")
        s = self.qe.stats()
        assert s["total_queries"] >= 1

    def test_history(self):
        self.qe.execute("SELECT 1")
        h = self.qe.get_history()
        assert len(h) >= 1


class TestPreparedStatementManager:
    def setup_method(self):
        self.psm = PreparedStatementManager()

    def test_prepare(self):
        stmt = self.psm.prepare("get_user", "SELECT * FROM users WHERE id = ?")
        assert stmt.sql.startswith("SELECT")

    def test_execute(self):
        self.psm.prepare("q", "SELECT 1")
        assert self.psm.execute("q") is True

    def test_drop(self):
        self.psm.prepare("q", "SELECT 1")
        assert self.psm.drop("q") is True
        assert self.psm.drop("q") is False

    def test_list_all(self):
        self.psm.prepare("a", "SELECT 1")
        self.psm.prepare("b", "SELECT 2")
        assert len(self.psm.list_all()) == 2

    def test_stats(self):
        self.psm.prepare("q", "SELECT 1")
        self.psm.execute("q")
        s = self.psm.stats()
        assert s["total_executions"] == 1


class TestORMBridge:
    def setup_method(self):
        self.bridge = ORMBridge()

    def test_set_framework(self):
        self.bridge.set_framework("django")
        assert self.bridge._framework == "django"

    def test_register_model(self):
        model = ORMModel("User", "users")
        model.add_field("id", "INTEGER PRIMARY KEY")
        self.bridge.register_model(model)
        assert self.bridge.get_model("User") is not None

    def test_to_create_table(self):
        model = ORMModel("User", "users")
        model.add_field("id", "INTEGER PRIMARY KEY")
        self.bridge.register_model(model)
        sql = self.bridge.to_create_table("User")
        assert "CREATE TABLE" in sql

    def test_get_all(self):
        self.bridge.register_model(ORMModel("A"))
        self.bridge.register_model(ORMModel("B"))
        assert len(self.bridge.get_all_models()) == 2


class TestSchemaManager:
    def setup_method(self):
        self.sm = SchemaManager()

    def test_create_table(self):
        schema = TableSchema("users")
        schema.add_column("id", "INTEGER", nullable=False)
        assert self.sm.create_table(schema) is True

    def test_drop_table(self):
        self.sm.create_table(TableSchema("users"))
        assert self.sm.drop_table("users") is True

    def test_alter_table(self):
        self.sm.create_table(TableSchema("users"))
        assert self.sm.alter_table("users", {"email": "VARCHAR"}) is True

    def test_list_tables(self):
        self.sm.create_table(TableSchema("a"))
        self.sm.create_table(TableSchema("b"))
        assert len(self.sm.list_tables()) == 2

    def test_get_history(self):
        self.sm.create_table(TableSchema("a"))
        h = self.sm.get_history()
        assert len(h) >= 1


class TestMigrationEngine:
    def setup_method(self):
        self.me = MigrationEngine()

    def test_add_migration(self):
        m = Migration("1.0.0", "init", "CREATE TABLE t (id INT)")
        self.me.add_migration(m)
        assert len(self.me.get_pending()) == 1

    def test_migrate_up(self):
        self.me.add_migration(Migration("1.0.0", "init", "CREATE TABLE t"))
        applied = self.me.migrate_up("1.0.0")
        assert len(applied) == 1
        assert self.me.get_current_version() == "1.0.0"

    def test_migrate_down(self):
        self.me.add_migration(Migration("1.0.0", "init", "CREATE TABLE t"))
        self.me.add_migration(Migration("2.0.0", "add", "ALTER TABLE t"))
        self.me.migrate_up("2.0.0")
        rolled = self.me.migrate_down("1.0.0")
        assert len(rolled) >= 1

    def test_stats(self):
        self.me.add_migration(Migration("1.0.0", "init", "SQL"))
        s = self.me.stats()
        assert s["total"] == 1


class TestIndexManager:
    def setup_method(self):
        self.im = IndexManager()

    def test_create_index(self):
        idx = DatabaseIndex("idx_users_email", "users", ["email"], unique=True)
        assert self.im.create_index(idx) is True

    def test_drop_index(self):
        self.im.create_index(DatabaseIndex("idx1", "users", ["id"]))
        assert self.im.drop_index("idx1") is True

    def test_get_indexes_for_table(self):
        self.im.create_index(DatabaseIndex("idx1", "users", ["id"]))
        self.im.create_index(DatabaseIndex("idx2", "posts", ["id"]))
        assert len(self.im.get_indexes_for_table("users")) == 1

    def test_stats(self):
        self.im.create_index(DatabaseIndex("idx1", "users", ["id"]))
        s = self.im.stats()
        assert s["total"] == 1


class TestPartitionManager:
    def setup_method(self):
        self.pm = PartitionManager()

    def test_create_partition(self):
        p = Partition("p_2024", "logs", "range", "created_at")
        assert self.pm.create_partition(p) is True

    def test_drop_partition(self):
        self.pm.create_partition(Partition("p1", "logs"))
        assert self.pm.drop_partition("p1") is True

    def test_get_for_table(self):
        self.pm.create_partition(Partition("p1", "logs"))
        self.pm.create_partition(Partition("p2", "events"))
        assert len(self.pm.get_partitions_for_table("logs")) == 1

    def test_stats(self):
        self.pm.create_partition(Partition("p1", "logs"))
        s = self.pm.stats()
        assert s["total"] == 1


class TestReplicationManager:
    def setup_method(self):
        self.rm = ReplicationManager()

    def test_enable_disable(self):
        self.rm.enable()
        assert self.rm._is_enabled is True
        self.rm.disable()
        assert self.rm._is_enabled is False

    def test_add_remove_replica(self):
        node = ReplicaNode("replica1.local", 5432)
        assert self.rm.add_replica(node) is True
        assert self.rm.remove_replica(node.node_id) is True

    def test_is_healthy(self):
        node = ReplicaNode("r1.local")
        self.rm.add_replica(node)
        assert self.rm.is_healthy() is True

    def test_stats(self):
        self.rm.add_replica(ReplicaNode("r1"))
        s = self.rm.stats()
        assert s["nodes"] == 1


class TestBackupManager:
    def setup_method(self):
        self.bm = BackupManager()

    def test_full_backup(self):
        job = self.bm.create_full_backup("mydb")
        assert job.status == "completed"
        assert job.backup_type == "full"

    def test_incremental(self):
        job = self.bm.create_incremental_backup("mydb")
        assert job.status == "completed"

    def test_get_job(self):
        job = self.bm.create_full_backup("db")
        found = self.bm.get_job(job.job_id)
        assert found is not None

    def test_stats(self):
        self.bm.create_full_backup("db")
        s = self.bm.stats()
        assert s["total_jobs"] == 1


class TestRestoreManager:
    def setup_method(self):
        self.rm = RestoreManager()

    def test_restore(self):
        job = self.rm.restore("mydb", "backup_001")
        assert job.status == "completed"

    def test_list_jobs(self):
        self.rm.restore("db", "b1")
        assert len(self.rm.list_jobs()) == 1


class TestQueryOptimizer:
    def setup_method(self):
        self.qo = QueryOptimizer()

    def test_analyze(self):
        suggestions = self.qo.analyze("SELECT * FROM users WHERE name LIKE '%test%'")
        assert len(suggestions) >= 1

    def test_get_all_suggestions(self):
        self.qo.analyze("SELECT * FROM users")
        assert len(self.qo.get_all_suggestions()) >= 1

    def test_rules(self):
        rules = self.qo.get_rules()
        assert len(rules) >= 3


class TestQueryAnalyzer:
    def setup_method(self):
        self.qa = QueryAnalyzer()

    def test_profile(self):
        p = self.qa.profile("SELECT 1", 5.0)
        assert p.execution_time_ms == 5.0

    def test_slow_queries(self):
        self.qa.profile("SELECT 1", 1.0)
        self.qa.profile("SELECT 2", 200.0)
        slow = self.qa.get_slow_queries(100.0)
        assert len(slow) == 1

    def test_stats(self):
        self.qa.profile("SELECT 1", 10.0)
        s = self.qa.stats()
        assert s["total_profiles"] == 1


class TestDeadlockDetector:
    def setup_method(self):
        self.dd = DeadlockDetector()

    def test_add_request(self):
        req = LockRequest("tx1", "table_a", "exclusive")
        self.dd.add_request(req)
        assert len(self.dd._requests) == 1

    def test_detect_no_deadlock(self):
        self.dd.add_request(LockRequest("tx1", "table_a", "shared"))
        self.dd.add_request(LockRequest("tx2", "table_b", "shared"))
        deadlocks = self.dd.detect()
        assert len(deadlocks) == 0

    def test_detect_deadlock(self):
        self.dd.add_request(LockRequest("tx1", "table_a", "exclusive"))
        self.dd.add_request(LockRequest("tx2", "table_a", "exclusive"))
        deadlocks = self.dd.detect()
        assert len(deadlocks) >= 1

    def test_clear(self):
        self.dd.add_request(LockRequest("tx1", "a"))
        self.dd.clear()
        assert len(self.dd._requests) == 0


class TestLockManager:
    def setup_method(self):
        self.lm = LockManager()

    def test_acquire(self):
        lock = self.lm.acquire("table_a", "shared", "tx1")
        assert lock is not None

    def test_acquire_exclusive_blocks(self):
        self.lm.acquire("table_a", "exclusive", "tx1")
        lock2 = self.lm.acquire("table_a", "shared", "tx2")
        assert lock2 is None

    def test_release(self):
        self.lm.acquire("table_a", "shared", "tx1")
        assert self.lm.release("table_a", "tx1") is True

    def test_is_locked(self):
        self.lm.acquire("table_a", "shared", "tx1")
        assert self.lm.is_locked("table_a") is True

    def test_clear_expired(self):
        self.lm.acquire("table_a", "shared", "tx1", timeout=0.0)
        import time
        time.sleep(0.01)
        count = self.lm.clear_expired()
        assert count >= 1

    def test_stats(self):
        self.lm.acquire("a", "shared", "tx1")
        s = self.lm.stats()
        assert s["active_locks"] == 1


class TestSQLMetrics:
    def setup_method(self):
        self.sm = SQLMetrics()

    def test_record(self):
        self.sm.record_query("SELECT", 5.0, True)
        assert self.sm._queries == 1

    def test_error_rate(self):
        self.sm.record_query("SELECT", 5.0, True)
        self.sm.record_query("SELECT", 5.0, False)
        assert self.sm.get_error_rate() == 0.5

    def test_avg_time(self):
        self.sm.record_query("SELECT", 10.0)
        self.sm.record_query("SELECT", 20.0)
        assert self.sm.get_avg_time() == 15.0

    def test_reset(self):
        self.sm.record_query("SELECT", 5.0)
        self.sm.reset()
        assert self.sm._queries == 0

    def test_to_dict(self):
        self.sm.record_query("SELECT", 5.0)
        d = self.sm.to_dict()
        assert "queries" in d


class TestSQLHealth:
    def setup_method(self):
        self.sh = SQLHealth()

    def test_check(self):
        result = self.sh.check("pool", True, 2.0)
        assert result["healthy"] is True

    def test_is_healthy(self):
        self.sh.check("pool", True)
        self.sh.check("replica", True)
        assert self.sh.is_healthy() is True

    def test_degraded(self):
        self.sh.check("pool", True)
        self.sh.check("replica", False)
        assert self.sh.is_healthy() is False

    def test_to_dict(self):
        self.sh.check("pool", True)
        d = self.sh.to_dict()
        assert "healthy" in d


class TestSQLReport:
    def setup_method(self):
        self.sr = SQLReport()

    def test_generate(self):
        report = self.sr.generate({"queries": 100}, {"healthy": True}, {"size": 5})
        assert "metrics" in report

    def test_history(self):
        self.sr.generate({}, {}, {})
        h = self.sr.get_history()
        assert len(h) == 1


# ═══════════════════════════════════════════════════════════════════════
# MODULE 3: Redis Platform
# ═══════════════════════════════════════════════════════════════════════

from layers.layer13_persistence.modules.redis_platform.redis_client import RedisClient
from layers.layer13_persistence.modules.redis_platform.cache_manager import CacheManager
from layers.layer13_persistence.modules.redis_platform.session_manager import SessionManager
from layers.layer13_persistence.modules.redis_platform.distributed_lock import DistributedLockManager
from layers.layer13_persistence.modules.redis_platform.pubsub import PubSub
from layers.layer13_persistence.modules.redis_platform.queue_manager import QueueManager
from layers.layer13_persistence.modules.redis_platform.stream_manager import StreamManager
from layers.layer13_persistence.modules.redis_platform.rate_limiter import RateLimiter
from layers.layer13_persistence.modules.redis_platform.ttl_manager import TTLManager
from layers.layer13_persistence.modules.redis_platform.cache_analytics import CacheAnalytics
from layers.layer13_persistence.modules.redis_platform.cluster_manager import ClusterManager, ClusterNode
from layers.layer13_persistence.modules.redis_platform.redis_health import RedisHealth
from layers.layer13_persistence.modules.redis_platform.redis_metrics import RedisMetrics
from layers.layer13_persistence.modules.redis_platform.redis_report import RedisReport


class TestRedisClient:
    def setup_method(self):
        self.rc = RedisClient()

    def test_connect(self):
        assert self.rc.connect() is True
        assert self.rc.is_connected() is True

    def test_disconnect(self):
        self.rc.connect()
        assert self.rc.disconnect() is True
        assert self.rc.is_connected() is False

    def test_set_get(self):
        self.rc.connect()
        self.rc.set("key1", "value1")
        assert self.rc.get("key1") == "value1"

    def test_delete(self):
        self.rc.connect()
        self.rc.set("key1", "value1")
        assert self.rc.delete("key1") is True
        assert self.rc.get("key1") is None

    def test_exists(self):
        self.rc.connect()
        self.rc.set("k", "v")
        assert self.rc.exists("k") is True

    def test_mget_mset(self):
        self.rc.connect()
        self.rc.mset({"a": "1", "b": "2"})
        vals = self.rc.mget(["a", "b", "c"])
        assert vals[0] == "1"
        assert vals[2] is None

    def test_incr_decr(self):
        self.rc.connect()
        self.rc.set("counter", "0")
        assert self.rc.incr("counter") == 1
        assert self.rc.decr("counter") == 0

    def test_flush(self):
        self.rc.connect()
        self.rc.set("a", "1")
        assert self.rc.flush() is True
        assert self.rc.dbsize() == 0

    def test_ping(self):
        self.rc.connect()
        assert self.rc.ping() is True


class TestCacheManager:
    def setup_method(self):
        self.cm = CacheManager(max_entries=100)

    def test_set_get(self):
        self.cm.set("k", "v")
        assert self.cm.get("k") == "v"

    def test_miss(self):
        assert self.cm.get("missing") is None

    def test_delete(self):
        self.cm.set("k", "v")
        assert self.cm.delete("k") is True
        assert self.cm.get("k") is None

    def test_exists(self):
        self.cm.set("k", "v")
        assert self.cm.exists("k") is True

    def test_lru_eviction(self):
        cm = CacheManager(max_entries=3)
        cm.set("a", "1")
        cm.set("b", "2")
        cm.set("c", "3")
        cm.set("d", "4")
        assert len(cm._cache) <= 3

    def test_invalidate_pattern(self):
        self.cm.set("user:1", "a")
        self.cm.set("user:2", "b")
        self.cm.set("post:1", "c")
        removed = self.cm.invalidate_pattern("user:*")
        assert removed == 2

    def test_flush(self):
        self.cm.set("a", "1")
        count = self.cm.flush()
        assert count >= 1

    def test_stats(self):
        self.cm.set("k", "v")
        self.cm.get("k")
        s = self.cm.get_stats()
        assert s["hits"] >= 1


class TestSessionManager:
    def setup_method(self):
        self.sm = SessionManager()

    def test_create_get(self):
        session = self.sm.create("s1", "user1")
        assert session.session_id == "s1"
        found = self.sm.get("s1")
        assert found is not None

    def test_destroy(self):
        self.sm.create("s1", "user1")
        assert self.sm.destroy("s1") is True
        assert self.sm.get("s1") is None

    def test_get_user_sessions(self):
        self.sm.create("s1", "u1")
        self.sm.create("s2", "u1")
        self.sm.create("s3", "u2")
        assert len(self.sm.get_user_sessions("u1")) == 2

    def test_active_count(self):
        self.sm.create("s1", "u1")
        assert self.sm.active_count() == 1


class TestDistributedLockManager:
    def setup_method(self):
        self.dlm = DistributedLockManager()

    def test_acquire(self):
        lock = self.dlm.acquire("resource1", "owner1")
        assert lock is not None

    def test_acquire_blocks(self):
        self.dlm.acquire("resource1", "owner1")
        lock2 = self.dlm.acquire("resource1", "owner2")
        assert lock2 is None

    def test_release(self):
        self.dlm.acquire("resource1", "owner1")
        assert self.dlm.release("resource1", "owner1") is True

    def test_is_locked(self):
        self.dlm.acquire("r1", "o1")
        assert self.dlm.is_locked("r1") is True

    def test_force_release(self):
        self.dlm.acquire("r1", "o1")
        assert self.dlm.force_release("r1") is True

    def test_stats(self):
        self.dlm.acquire("r1", "o1")
        s = self.dlm.stats()
        assert s["active_locks"] == 1


class TestPubSub:
    def setup_method(self):
        self.ps = PubSub()

    def test_subscribe_publish(self):
        received = []
        self.ps.subscribe("channel1", lambda m: received.append(m.data))
        self.ps.publish("channel1", "hello")
        assert len(received) == 1
        assert received[0] == "hello"

    def test_unsubscribe(self):
        handler = lambda m: None
        self.ps.subscribe("ch", handler)
        assert self.ps.unsubscribe("ch", handler) is True

    def test_messages(self):
        self.ps.publish("ch", "m1")
        self.ps.publish("ch", "m2")
        msgs = self.ps.get_messages("ch")
        assert len(msgs) == 2

    def test_stats(self):
        self.ps.subscribe("ch", lambda m: None)
        s = self.ps.stats()
        assert s["channels"] == 1


class TestQueueManager:
    def setup_method(self):
        self.qm = QueueManager()

    def test_enqueue_dequeue(self):
        self.qm.enqueue("q1", "item1")
        item = self.qm.dequeue("q1")
        assert item is not None
        assert item.data == "item1"

    def test_priority(self):
        self.qm.enqueue("q1", "low", priority=1)
        self.qm.enqueue("q1", "high", priority=10)
        item = self.qm.dequeue("q1")
        assert item.data == "high"

    def test_peek(self):
        self.qm.enqueue("q1", "item1")
        item = self.qm.peek("q1")
        assert item.data == "item1"
        assert self.qm.size("q1") == 1

    def test_dequeue_empty(self):
        assert self.qm.dequeue("empty") is None

    def test_stats(self):
        self.qm.enqueue("q1", "a")
        s = self.qm.stats()
        assert s["queues"] == 1


class TestStreamManager:
    def setup_method(self):
        self.sm = StreamManager()

    def test_add_read(self):
        self.sm.add("stream1", {"event": "login"})
        entries = self.sm.read("stream1")
        assert len(entries) == 1

    def test_trim(self):
        for i in range(10):
            self.sm.add("stream1", {"i": str(i)})
        self.sm.trim("stream1", 5)
        assert self.sm.length("stream1") == 5

    def test_delete(self):
        self.sm.add("s1", {"a": "b"})
        assert self.sm.delete_stream("s1") is True

    def test_list_streams(self):
        self.sm.add("s1", {"a": "b"})
        assert "s1" in self.sm.list_streams()


class TestRateLimiter:
    def setup_method(self):
        self.rl = RateLimiter(max_requests=3, window_seconds=1.0)

    def test_allow(self):
        assert self.rl.is_allowed("user1") is True

    def test_block(self):
        for _ in range(3):
            self.rl.is_allowed("user1")
        assert self.rl.is_allowed("user1") is False

    def test_remaining(self):
        self.rl.is_allowed("u1")
        remaining = self.rl.get_remaining("u1")
        assert remaining == 2

    def test_reset(self):
        for _ in range(3):
            self.rl.is_allowed("u1")
        self.rl.reset("u1")
        assert self.rl.is_allowed("u1") is True


class TestTTLManager:
    def setup_method(self):
        self.ttl = TTLManager()

    def test_set_get(self):
        self.ttl.set("k", 60)
        remaining = self.ttl.get_ttl("k")
        assert remaining is not None
        assert remaining > 0

    def test_expired(self):
        self.ttl.set("k", 0)
        import time
        time.sleep(0.01)
        assert self.ttl.is_expired("k") is True

    def test_delete(self):
        self.ttl.set("k", 60)
        assert self.ttl.delete("k") is True

    def test_cleanup(self):
        self.ttl.set("k1", 0)
        import time
        time.sleep(0.01)
        count = self.ttl.cleanup_expired()
        assert count >= 1


class TestCacheAnalytics:
    def setup_method(self):
        self.ca = CacheAnalytics()

    def test_hit_miss(self):
        self.ca.record_hit("user:1")
        self.ca.record_miss("user:2")
        rate = self.ca.get_hit_rate()
        assert rate == 0.5

    def test_pattern_stats(self):
        self.ca.record_hit("user:1")
        self.ca.record_miss("user:2")
        ps = self.ca.get_pattern_stats()
        assert "user" in ps

    def test_to_dict(self):
        self.ca.record_hit("k")
        d = self.ca.to_dict()
        assert "hit_rate" in d


class TestClusterManager:
    def setup_method(self):
        self.cm = ClusterManager()

    def test_enable_disable(self):
        self.cm.enable_cluster()
        assert self.cm._is_cluster is True

    def test_add_remove_node(self):
        node = ClusterNode("node1.local", 6379, "master")
        assert self.cm.add_node(node) is True
        assert self.cm.remove_node(node.node_id) is True

    def test_get_masters_replicas(self):
        self.cm.add_node(ClusterNode("m1", 6379, "master"))
        self.cm.add_node(ClusterNode("r1", 6380, "replica"))
        assert len(self.cm.get_masters()) == 1
        assert len(self.cm.get_replicas()) == 1

    def test_is_healthy(self):
        self.cm.add_node(ClusterNode("n1"))
        assert self.cm.is_healthy() is True

    def test_stats(self):
        self.cm.add_node(ClusterNode("n1"))
        s = self.cm.stats()
        assert s["nodes"] == 1


class TestRedisHealth:
    def setup_method(self):
        self.rh = RedisHealth()

    def test_check(self):
        result = self.rh.check("connection", True, 1.5)
        assert result["healthy"] is True

    def test_is_healthy(self):
        self.rh.check("conn", True)
        self.rh.check("memory", True)
        assert self.rh.is_healthy() is True

    def test_degraded(self):
        self.rh.check("conn", True)
        self.rh.check("memory", False)
        assert self.rh.is_healthy() is False


class TestRedisMetrics:
    def setup_method(self):
        self.rm = RedisMetrics()

    def test_record(self):
        self.rm.record("GET", 0.5, True)
        assert self.rm._operations == 1

    def test_error_rate(self):
        self.rm.record("GET", 0.5, True)
        self.rm.record("SET", 0.5, False)
        assert self.rm.get_error_rate() == 0.5

    def test_reset(self):
        self.rm.record("GET", 0.5)
        self.rm.reset()
        assert self.rm._operations == 0

    def test_to_dict(self):
        self.rm.record("GET", 0.5)
        d = self.rm.to_dict()
        assert "operations" in d


class TestRedisReport:
    def setup_method(self):
        self.rr = RedisReport()

    def test_generate(self):
        report = self.rr.generate({"ops": 100}, {"healthy": True}, {"entries": 50})
        assert "metrics" in report

    def test_history(self):
        self.rr.generate({}, {}, {})
        h = self.rr.get_history()
        assert len(h) == 1


# ═══════════════════════════════════════════════════════════════════════
# MODULE 4: Vector Database Platform
# ═══════════════════════════════════════════════════════════════════════

from layers.layer13_persistence.modules.vector_database_platform.embedding_manager import EmbeddingManager
from layers.layer13_persistence.modules.vector_database_platform.vector_store import VectorStore
from layers.layer13_persistence.modules.vector_database_platform.similarity_search import SimilaritySearch
from layers.layer13_persistence.modules.vector_database_platform.hybrid_search import HybridSearch
from layers.layer13_persistence.modules.vector_database_platform.metadata_search import MetadataSearch
from layers.layer13_persistence.modules.vector_database_platform.collection_manager import CollectionManager
from layers.layer13_persistence.modules.vector_database_platform.vector_index import VectorIndex
from layers.layer13_persistence.modules.vector_database_platform.vector_backup import VectorBackupManager
from layers.layer13_persistence.modules.vector_database_platform.embedding_cache import EmbeddingCache
from layers.layer13_persistence.modules.vector_database_platform.embedding_generator import EmbeddingGenerator
from layers.layer13_persistence.modules.vector_database_platform.embedding_validator import EmbeddingValidator


class TestEmbeddingManager:
    def setup_method(self):
        self.em = EmbeddingManager()

    def test_generate(self):
        result = self.em.generate("hello world")
        assert result.dimensions == 1536
        assert len(result.vector) == 1536

    def test_batch_generate(self):
        results = self.em.batch_generate(["a", "b", "c"])
        assert len(results) == 3

    def test_get(self):
        result = self.em.generate("test")
        found = self.em.get(result.embedding_id)
        assert found is not None

    def test_delete(self):
        result = self.em.generate("test")
        assert self.em.delete(result.embedding_id) is True
        assert self.em.delete(result.embedding_id) is False

    def test_similarity(self):
        a = self.em.generate("hello")
        b = self.em.generate("hello")
        sim = self.em.similarity(a, b)
        assert sim > 0.99

    def test_cache_hit(self):
        a = self.em.generate("cached_text")
        b = self.em.generate("cached_text")
        assert a.embedding_id == b.embedding_id

    def test_stats(self):
        self.em.generate("test")
        s = self.em.stats()
        assert s["embeddings"] == 1


class TestVectorStore:
    def setup_method(self):
        self.vs = VectorStore(dimensions=128)

    def test_upsert(self):
        vec = [0.1] * 128
        record = self.vs.upsert(vec, {"source": "test"})
        assert record.record_id > 0

    def test_search(self):
        vec1 = [1.0] + [0.0] * 127
        vec2 = [0.0] + [1.0] * 127
        self.vs.upsert(vec1, {"label": "a"})
        self.vs.upsert(vec2, {"label": "b"})
        results = self.vs.search(vec1, top_k=1)
        assert len(results) == 1
        assert results[0][0].metadata["label"] == "a"

    def test_search_with_filter(self):
        vec = [0.5] * 128
        self.vs.upsert(vec, {"type": "a"})
        self.vs.upsert(vec, {"type": "b"})
        results = self.vs.search(vec, top_k=10, filter_metadata={"type": "a"})
        assert all(r.metadata["type"] == "a" for r, _ in results)

    def test_delete(self):
        record = self.vs.upsert([0.1] * 128)
        assert self.vs.delete(record.record_id) is True

    def test_count(self):
        self.vs.upsert([0.1] * 128)
        self.vs.upsert([0.2] * 128)
        assert self.vs.count() == 2


class TestSimilaritySearch:
    def setup_method(self):
        self.ss = SimilaritySearch()

    def test_cosine(self):
        vectors = [(1, [1.0, 0.0, 0.0]), (2, [0.0, 1.0, 0.0]), (3, [1.0, 0.0, 0.0])]
        results = self.ss.search([1.0, 0.0, 0.0], vectors, top_k=2)
        assert results[0][0] == 1

    def test_euclidean(self):
        self.ss.set_metric("euclidean")
        vectors = [(1, [1.0, 0.0]), (2, [0.0, 1.0])]
        results = self.ss.search([1.0, 0.0], vectors, top_k=1)
        assert results[0][0] == 1

    def test_batch_search(self):
        vectors = [(1, [1.0, 0.0]), (2, [0.0, 1.0])]
        queries = [[1.0, 0.0], [0.0, 1.0]]
        results = self.ss.batch_search(queries, vectors, top_k=1)
        assert len(results) == 2


class TestHybridSearch:
    def setup_method(self):
        self.hs = HybridSearch(vector_weight=0.5, keyword_weight=0.5)

    def test_search(self):
        records = [
            {"id": 1, "vector": [1.0, 0.0], "text": "machine learning guide"},
            {"id": 2, "vector": [0.0, 1.0], "text": "cooking recipes"},
        ]
        results = self.hs.search([1.0, 0.0], ["machine", "learning"], records, top_k=1)
        assert results[0]["id"] == 1


class TestMetadataSearch:
    def setup_method(self):
        self.ms = MetadataSearch()

    def test_filter_eq(self):
        records = [
            {"metadata": {"type": "a", "score": 0.9}},
            {"metadata": {"type": "b", "score": 0.5}},
        ]
        results = self.ms.filter(records, {"type": "a"})
        assert len(results) == 1

    def test_filter_gt(self):
        records = [
            {"metadata": {"score": 0.9}},
            {"metadata": {"score": 0.5}},
        ]
        results = self.ms.filter(records, {"score": {"gt": 0.7}})
        assert len(results) == 1

    def test_filter_in(self):
        records = [
            {"metadata": {"status": "active"}},
            {"metadata": {"status": "deleted"}},
        ]
        results = self.ms.filter(records, {"status": {"in": ["active", "pending"]}})
        assert len(results) == 1


class TestCollectionManager:
    def setup_method(self):
        self.cm = CollectionManager()

    def test_create(self):
        col = self.cm.create("docs", 768)
        assert col.name == "docs"
        assert col.dimensions == 768

    def test_delete(self):
        self.cm.create("docs")
        assert self.cm.delete("docs") is True
        assert self.cm.delete("docs") is False

    def test_get(self):
        self.cm.create("docs")
        assert self.cm.get("docs") is not None
        assert self.cm.get("missing") is None

    def test_list(self):
        self.cm.create("a")
        self.cm.create("b")
        assert self.cm.count() == 2

    def test_stats(self):
        self.cm.create("a")
        s = self.cm.stats()
        assert s["collections"] == 1


class TestVectorIndex:
    def setup_method(self):
        self.vi = VectorIndex(dimensions=3)

    def test_add(self):
        self.vi.add(1, [1.0, 0.0, 0.0])
        assert self.vi.count() == 1

    def test_search(self):
        self.vi.add(1, [1.0, 0.0, 0.0])
        self.vi.add(2, [0.0, 1.0, 0.0])
        results = self.vi.search([1.0, 0.0, 0.0], top_k=1)
        assert results[0][0] == 1

    def test_remove(self):
        self.vi.add(1, [1.0, 0.0, 0.0])
        assert self.vi.remove(1) is True
        assert self.vi.count() == 0

    def test_rebuild(self):
        assert self.vi.rebuild() is True


class TestVectorBackupManager:
    def setup_method(self):
        self.vbm = VectorBackupManager()

    def test_create_backup(self):
        b = self.vbm.create_backup("docs", 1000)
        assert b.record_count == 1000

    def test_get_backup(self):
        b = self.vbm.create_backup("docs", 500)
        found = self.vbm.get_backup(b.backup_id)
        assert found is not None

    def test_list_backups(self):
        self.vbm.create_backup("docs", 100)
        self.vbm.create_backup("images", 200)
        assert len(self.vbm.list_backups("docs")) == 1

    def test_stats(self):
        self.vbm.create_backup("docs", 100)
        s = self.vbm.stats()
        assert s["backups"] == 1


class TestEmbeddingCache:
    def setup_method(self):
        self.ec = EmbeddingCache(max_size=100)

    def test_set_get(self):
        self.ec.set("hello", [0.1, 0.2])
        result = self.ec.get("hello")
        assert result == [0.1, 0.2]

    def test_miss(self):
        assert self.ec.get("missing") is None

    def test_invalidate(self):
        self.ec.set("hello", [0.1])
        assert self.ec.invalidate("hello") is True
        assert self.ec.get("hello") is None

    def test_flush(self):
        self.ec.set("a", [0.1])
        count = self.ec.flush()
        assert count == 1

    def test_stats(self):
        self.ec.set("k", [0.1])
        self.ec.get("k")
        s = self.ec.get_stats()
        assert s["hits"] >= 1


class TestEmbeddingGenerator:
    def setup_method(self):
        self.eg = EmbeddingGenerator()

    def test_register_model(self):
        self.eg.register_model("gpt", 1536, "OpenAI embedding")
        assert "gpt" in self.eg.get_models()

    def test_generate(self):
        result = self.eg.generate("test text")
        assert result.dimensions > 0

    def test_batch(self):
        results = self.eg.batch_generate(["a", "b"])
        assert len(results) == 2

    def test_stats(self):
        self.eg.generate("test")
        s = self.eg.stats()
        assert "cache" in s


class TestEmbeddingValidator:
    def setup_method(self):
        self.ev = EmbeddingValidator(expected_dimensions=3)

    def test_valid(self):
        assert self.ev.is_valid([0.1, 0.2, 0.3]) is True

    def test_invalid_dimension(self):
        errors = self.ev.validate([0.1, 0.2])
        assert len(errors) > 0

    def test_validate_batch(self):
        result = self.ev.validate_batch([[0.1, 0.2, 0.3], [0.1, 0.2]])
        assert result["valid"] == 1
        assert result["invalid"] == 1

    def test_fix(self):
        fixed = self.ev.fix([0.1, 0.2])
        assert len(fixed) == 3


# ═══════════════════════════════════════════════════════════════════════
# MODULE 5: Object Storage Platform
# ═══════════════════════════════════════════════════════════════════════

from layers.layer13_persistence.modules.object_storage_platform.storage_manager import StorageManager
from layers.layer13_persistence.modules.object_storage_platform.upload_engine import UploadEngine
from layers.layer13_persistence.modules.object_storage_platform.download_engine import DownloadEngine
from layers.layer13_persistence.modules.object_storage_platform.compression_engine import CompressionEngine
from layers.layer13_persistence.modules.object_storage_platform.encryption_engine import EncryptionEngine
from layers.layer13_persistence.modules.object_storage_platform.metadata_manager import MetadataManager
from layers.layer13_persistence.modules.object_storage_platform.lifecycle_manager import LifecycleManager, LifecycleRule
from layers.layer13_persistence.modules.object_storage_platform.cdn_manager import CDNManager, CDNConfig
from layers.layer13_persistence.modules.object_storage_platform.file_versioning import FileVersionManager
from layers.layer13_persistence.modules.object_storage_platform.chunk_uploader import ChunkUploader
from layers.layer13_persistence.modules.object_storage_platform.multipart_uploader import MultipartUploader
from layers.layer13_persistence.modules.object_storage_platform.storage_analytics import StorageAnalytics
from layers.layer13_persistence.modules.object_storage_platform.storage_metrics import StorageMetrics
from layers.layer13_persistence.modules.object_storage_platform.storage_health import StorageHealth


class TestStorageManager:
    def setup_method(self):
        self.sm = StorageManager()

    def test_put_get(self):
        obj = self.sm.put("bucket1", "key1", b"data", "text/plain")
        found = self.sm.get("bucket1", "key1")
        assert found is not None
        assert found.key == "key1"

    def test_delete(self):
        self.sm.put("b", "k", b"data")
        assert self.sm.delete("b", "k") is True
        assert self.sm.get("b", "k") is None

    def test_exists(self):
        self.sm.put("b", "k", b"data")
        assert self.sm.exists("b", "k") is True
        assert self.sm.exists("b", "missing") is False

    def test_list_objects(self):
        self.sm.put("b", "a/1", b"1")
        self.sm.put("b", "a/2", b"2")
        self.sm.put("b", "c/3", b"3")
        assert len(self.sm.list_objects("b", "a/")) == 2

    def test_count(self):
        self.sm.put("b", "k1", b"1")
        self.sm.put("b", "k2", b"2")
        assert self.sm.count("b") == 2
        assert self.sm.count() == 2

    def test_total_size(self):
        self.sm.put("b", "k1", b"hello")
        assert self.sm.total_size() == 5

    def test_stats(self):
        self.sm.put("b", "k", b"data")
        s = self.sm.stats()
        assert s["objects"] == 1


class TestUploadEngine:
    def setup_method(self):
        self.ue = UploadEngine()

    def test_upload(self):
        result = self.ue.upload("bucket", "key", b"data")
        assert result.status == "completed"
        assert result.size_bytes == 4

    def test_stats(self):
        self.ue.upload("b", "k", b"data")
        s = self.ue.stats()
        assert s["uploads"] == 1


class TestDownloadEngine:
    def setup_method(self):
        self.de = DownloadEngine()

    def test_download(self):
        result = self.de.download("bucket", "key", 100)
        assert result.status == "completed"

    def test_stats(self):
        self.de.download("b", "k", 100)
        s = self.de.stats()
        assert s["total_bytes"] == 100


class TestCompressionEngine:
    def setup_method(self):
        self.ce = CompressionEngine()

    def test_compress_decompress(self):
        original = b"Hello world! " * 100
        compressed = self.ce.compress(original)
        decompressed = self.ce.decompress(compressed)
        assert decompressed == original

    def test_ratio(self):
        original = b"aaa" * 100
        compressed = self.ce.compress(original)
        ratio = self.ce.ratio(original, compressed)
        assert ratio <= 1.0

    def test_algorithms(self):
        assert "gzip" in self.ce.get_algorithms()


class TestEncryptionEngine:
    def setup_method(self):
        self.ee = EncryptionEngine()

    def test_encrypt_decrypt(self):
        original = b"secret data"
        encrypted = self.ee.encrypt(original, "key123")
        decrypted = self.ee.decrypt(encrypted, "key123")
        assert decrypted == original

    def test_hash(self):
        h = self.ee.hash(b"test")
        assert len(h) == 64

    def test_algorithm(self):
        assert self.ee.get_algorithm() == "aes256"


class TestMetadataManager:
    def setup_method(self):
        self.mm = MetadataManager()

    def test_set_get(self):
        self.mm.set_metadata("obj1", "color", "red")
        assert self.mm.get_value("obj1", "color") == "red"

    def test_tags(self):
        self.mm.set_tags("obj1", ["important", "v2"])
        found = self.mm.search_by_tag("important")
        assert "obj1" in found

    def test_delete(self):
        self.mm.set_metadata("obj1", "k", "v")
        assert self.mm.delete("obj1") is True

    def test_count(self):
        self.mm.set_metadata("o1", "k", "v")
        assert self.mm.count() == 1


class TestLifecycleManager:
    def setup_method(self):
        self.lm = LifecycleManager()

    def test_add_rule(self):
        rule = LifecycleRule("logs/", expiration_days=90)
        self.lm.add_rule(rule)
        assert self.lm.count() == 1

    def test_evaluate(self):
        self.lm.add_rule(LifecycleRule("logs/", expiration_days=30))
        assert self.lm.evaluate("logs/2024.log", 31) == "expired"
        assert self.lm.evaluate("logs/2024.log", 15) is None

    def test_transition(self):
        self.lm.add_rule(LifecycleRule("data/", transition_days=30, storage_class="cold"))
        assert self.lm.evaluate("data/file.bin", 31) == "cold"

    def test_remove_rule(self):
        rule = LifecycleRule()
        self.lm.add_rule(rule)
        assert self.lm.remove_rule(rule.rule_id) is True


class TestCDNManager:
    def setup_method(self):
        self.cdn = CDNManager()

    def test_add_config(self):
        config = CDNConfig("cloudflare", "cdn.example.com")
        self.cdn.add_config("main", config)
        assert self.cdn.get_config("main") is not None

    def test_get_url(self):
        self.cdn.add_config("main", CDNConfig("cloudflare", "cdn.example.com"))
        url = self.cdn.get_url("main", "image.png")
        assert url == "https://cdn.example.com/image.png"

    def test_cache_ttl(self):
        self.cdn.set_cache_ttl("images/*", 86400)
        assert self.cdn.get_cache_ttl("images/*") == 86400


class TestFileVersionManager:
    def setup_method(self):
        self.fvm = FileVersionManager()

    def test_add_version(self):
        v = self.fvm.add_version("bucket", "key.txt", 100)
        assert v.is_latest is True

    def test_get_latest(self):
        self.fvm.add_version("b", "k", 100)
        self.fvm.add_version("b", "k", 200)
        latest = self.fvm.get_latest("b", "k")
        assert latest.size_bytes == 200
        assert latest.is_latest is True

    def test_total_versions(self):
        self.fvm.add_version("b", "k1", 100)
        self.fvm.add_version("b", "k2", 200)
        assert self.fvm.total_versions() == 2


class TestChunkUploader:
    def setup_method(self):
        self.cu = ChunkUploader(chunk_size=1024)

    def test_start_add(self):
        self.cu.start_upload("u1")
        self.cu.add_chunk("u1", 1, 500)
        self.cu.add_chunk("u1", 2, 500)
        assert self.cu.is_complete("u1", 2) is True

    def test_calculate_chunks(self):
        assert self.cu.calculate_chunks(3000) == 3
        assert self.cu.calculate_chunks(500) == 1

    def test_delete(self):
        self.cu.start_upload("u1")
        assert self.cu.delete_upload("u1") is True


class TestMultipartUploader:
    def setup_method(self):
        self.mu = MultipartUploader()

    def test_initiate(self):
        upload = self.mu.initiate("bucket", "large_file.bin")
        assert upload.status == "in_progress"

    def test_add_part_complete(self):
        upload = self.mu.initiate("b", "k")
        self.mu.add_part(upload.upload_id, 1)
        self.mu.add_part(upload.upload_id, 2)
        assert self.mu.complete(upload.upload_id) is True
        assert upload.status == "completed"

    def test_abort(self):
        upload = self.mu.initiate("b", "k")
        assert self.mu.abort(upload.upload_id) is True

    def test_list(self):
        self.mu.initiate("b", "k1")
        self.mu.initiate("b", "k2")
        assert len(self.mu.list_uploads()) == 2


class TestStorageAnalytics:
    def setup_method(self):
        self.sa = StorageAnalytics()

    def test_record(self):
        self.sa.record_operation("upload", "bucket", 1000)
        assert self.sa.get_total_operations() == 1

    def test_bucket_stats(self):
        self.sa.record_operation("upload", "b", 500)
        s = self.sa.get_bucket_stats("b")
        assert s["uploads"] == 1

    def test_total_bytes(self):
        self.sa.record_operation("upload", "b", 500)
        self.sa.record_operation("download", "b", 300)
        assert self.sa.get_total_bytes() == 800


class TestStorageMetrics:
    def setup_method(self):
        self.sm = StorageMetrics()

    def test_record(self):
        self.sm.record_object(100)
        self.sm.record_operation("upload")
        assert self.sm._total_objects == 1

    def test_error_rate(self):
        self.sm.record_operation("upload", True)
        self.sm.record_operation("upload", False)
        assert self.sm.get_error_rate() == 0.5

    def test_reset(self):
        self.sm.record_object(100)
        self.sm.reset()
        assert self.sm._total_objects == 0

    def test_to_dict(self):
        self.sm.record_object(100)
        d = self.sm.to_dict()
        assert "objects" in d


class TestStorageHealth:
    def setup_method(self):
        self.sh = StorageHealth()

    def test_check(self):
        result = self.sh.check("s3", True, 5.0)
        assert result["healthy"] is True

    def test_is_healthy(self):
        self.sh.check("s3", True)
        assert self.sh.is_healthy() is True

    def test_degraded(self):
        self.sh.check("s3", True)
        self.sh.check("minio", False)
        assert self.sh.is_healthy() is False


# ═══════════════════════════════════════════════════════════════════════
# MODULE 6: AI Memory Persistence
# ═══════════════════════════════════════════════════════════════════════

from layers.layer13_persistence.modules.ai_memory_persistence.conversation_memory_store import ConversationMemoryStore
from layers.layer13_persistence.modules.ai_memory_persistence.semantic_memory_store import SemanticMemoryStore
from layers.layer13_persistence.modules.ai_memory_persistence.episodic_memory_store import EpisodicMemoryStore, EpisodicMemory
from layers.layer13_persistence.modules.ai_memory_persistence.business_memory_store import BusinessMemoryStore
from layers.layer13_persistence.modules.ai_memory_persistence.knowledge_memory_store import KnowledgeMemoryStore
from layers.layer13_persistence.modules.ai_memory_persistence.prompt_memory_store import PromptMemoryStore
from layers.layer13_persistence.modules.ai_memory_persistence.learning_memory_store import LearningMemoryStore, Lesson
from layers.layer13_persistence.modules.ai_memory_persistence.strategy_memory_store import StrategyMemoryStore
from layers.layer13_persistence.modules.ai_memory_persistence.brand_memory_store import BrandMemoryStore
from layers.layer13_persistence.modules.ai_memory_persistence.analytics_memory_store import AnalyticsMemoryStore
from layers.layer13_persistence.modules.ai_memory_persistence.research_memory_store import ResearchMemoryStore
from layers.layer13_persistence.modules.ai_memory_persistence.context_memory_store import ContextMemoryStore
from layers.layer13_persistence.modules.ai_memory_persistence.working_memory_store import WorkingMemoryStore
from layers.layer13_persistence.modules.ai_memory_persistence.goal_memory_store import GoalMemoryStore, Goal
from layers.layer13_persistence.modules.ai_memory_persistence.memory_recovery import MemoryRecovery
from layers.layer13_persistence.modules.ai_memory_persistence.memory_snapshot import MemorySnapshotManager
from layers.layer13_persistence.modules.ai_memory_persistence.memory_version import MemoryVersionManager
from layers.layer13_persistence.modules.ai_memory_persistence.memory_compaction import MemoryCompactor
from layers.layer13_persistence.modules.ai_memory_persistence.memory_indexer import MemoryIndexer
from layers.layer13_persistence.modules.ai_memory_persistence.memory_search import MemorySearch


class TestConversationMemoryStore:
    def setup_method(self):
        self.store = ConversationMemoryStore()

    def test_store_retrieve(self):
        entry = self.store.store("conv1", {"role": "user", "content": "hi"})
        found = self.store.retrieve("conv1")
        assert found is not None

    def test_add_message(self):
        self.store.add_message("c1", "user", "hello")
        self.store.add_message("c1", "assistant", "hi there")
        msgs = self.store.get_conversation("c1")
        assert len(msgs) == 2

    def test_recent_messages(self):
        for i in range(20):
            self.store.add_message("c1", "user", f"msg{i}")
        recent = self.store.get_recent_messages("c1", 5)
        assert len(recent) == 5

    def test_conversation_count(self):
        self.store.add_message("c1", "user", "a")
        self.store.add_message("c2", "user", "b")
        assert self.store.conversation_count() == 2


class TestSemanticMemoryStore:
    def setup_method(self):
        self.store = SemanticMemoryStore()

    def test_store_retrieve(self):
        self.store.store("fact1", "Python is a programming language")
        entry = self.store.retrieve("fact1")
        assert entry is not None

    def test_with_embedding(self):
        emb = [0.1, 0.2, 0.3]
        self.store.store_with_embedding("fact1", "test", emb)
        found = self.store.get_embedding("fact1")
        assert found == emb

    def test_similarity_search(self):
        self.store.store_with_embedding("a", "hello", [1.0, 0.0, 0.0])
        self.store.store_with_embedding("b", "world", [0.0, 1.0, 0.0])
        results = self.store.search_by_similarity([1.0, 0.0, 0.0], top_k=1)
        assert results[0].key == "a"


class TestEpisodicMemoryStore:
    def setup_method(self):
        self.store = EpisodicMemoryStore()

    def test_store_retrieve(self):
        self.store.store("e1", "Published post")
        assert self.store.retrieve("e1") is not None

    def test_store_episode(self):
        ep = EpisodicMemory("User liked post", {"platform": "facebook"}, "engagement up")
        ep.importance = 0.9
        self.store.store_episode("e1", ep)
        found = self.store.get_episode("e1")
        assert found.importance == 0.9

    def test_search_by_importance(self):
        ep1 = EpisodicMemory("minor event")
        ep1.importance = 0.2
        ep2 = EpisodicMemory("major event")
        ep2.importance = 0.9
        self.store.store_episode("e1", ep1)
        self.store.store_episode("e2", ep2)
        results = self.store.search_by_importance(0.5)
        assert len(results) == 1

    def test_recent(self):
        for i in range(5):
            self.store.store_episode(f"e{i}", EpisodicMemory(f"event{i}"))
        recent = self.store.get_recent(3)
        assert len(recent) == 3


class TestBusinessMemoryStore:
    def setup_method(self):
        self.store = BusinessMemoryStore()

    def test_store_retrieve(self):
        self.store.store("b1", {"campaign": "summer_sale"})
        assert self.store.retrieve("b1") is not None

    def test_campaigns(self):
        self.store.store_campaign("c1", {"name": "Summer Sale", "budget": 5000})
        c = self.store.get_campaign("c1")
        assert c["budget"] == 5000

    def test_revenue(self):
        self.store.record_revenue(100.0, "ads")
        self.store.record_revenue(200.0, "sponsorship")
        assert self.store.total_revenue() == 300.0


class TestKnowledgeMemoryStore:
    def setup_method(self):
        self.store = KnowledgeMemoryStore()

    def test_store_retrieve(self):
        self.store.store("k1", "AI content agent architecture")
        assert self.store.retrieve("k1") is not None

    def test_graph(self):
        g = self.store.get_graph()
        g.add_entity("Python", "language")
        g.add_entity("AI", "field")
        g.add_relationship("Python", "AI", "used_in")
        assert g.entity_count() == 2
        assert g.relationship_count() == 1


class TestPromptMemoryStore:
    def setup_method(self):
        self.store = PromptMemoryStore()

    def test_store_retrieve(self):
        self.store.store("p1", "Write a tweet about AI")
        assert self.store.retrieve("p1") is not None

    def test_performance(self):
        self.store.store("p1", "prompt1")
        self.store.record_performance("p1", 0.8)
        self.store.record_performance("p1", 0.9)
        perf = self.store.get_performance("p1")
        assert perf["count"] == 2

    def test_best_prompts(self):
        self.store.store("p1", "prompt1")
        self.store.store("p2", "prompt2")
        self.store.record_performance("p1", 0.9)
        self.store.record_performance("p2", 0.5)
        best = self.store.get_best_prompts(1)
        assert best[0].key == "p1"


class TestLearningMemoryStore:
    def setup_method(self):
        self.store = LearningMemoryStore()

    def test_store_retrieve(self):
        self.store.store("l1", "Shorter captions get more engagement")
        assert self.store.retrieve("l1") is not None

    def test_lessons(self):
        lesson = Lesson("writing", "Keep posts under 150 words", "high")
        lesson.confidence = 0.85
        self.store.add_lesson(lesson)
        lessons = self.store.get_lessons("writing")
        assert len(lessons) == 1

    def test_mistakes(self):
        self.store.record_mistake({"type": "grammar", "text": "typo"})
        mistakes = self.store.get_mistakes()
        assert len(mistakes) == 1


class TestStrategyMemoryStore:
    def setup_method(self):
        self.store = StrategyMemoryStore()

    def test_store_retrieve(self):
        self.store.store("s1", "Video content strategy")
        assert self.store.retrieve("s1") is not None

    def test_outcomes(self):
        self.store.record_outcome("s1", {"score": 0.8, "engagement": "high"})
        self.store.record_outcome("s1", {"score": 0.6, "engagement": "medium"})
        outcomes = self.store.get_outcomes("s1")
        assert len(outcomes) == 2

    def test_best(self):
        self.store.record_outcome("s1", {"score": 0.5})
        self.store.record_outcome("s2", {"score": 0.9})
        assert self.store.get_best_strategy() == "s2"


class TestBrandMemoryStore:
    def setup_method(self):
        self.store = BrandMemoryStore()

    def test_store_retrieve(self):
        self.store.store("br1", "Professional tone")
        assert self.store.retrieve("br1") is not None

    def test_guidelines(self):
        self.store.set_guideline("tone", "Professional yet friendly")
        assert self.store.get_guideline("tone") == "Professional yet friendly"

    def test_voice_samples(self):
        self.store.add_voice_sample({"text": "We're excited to announce...", "platform": "linkedin"})
        samples = self.store.get_voice_samples()
        assert len(samples) == 1


class TestAnalyticsMemoryStore:
    def setup_method(self):
        self.store = AnalyticsMemoryStore()

    def test_store_retrieve(self):
        self.store.store("a1", {"metric": "engagement"})
        assert self.store.retrieve("a1") is not None

    def test_time_series(self):
        self.store.record_metric("engagement", 0.8)
        self.store.record_metric("engagement", 0.9)
        ts = self.store.get_time_series("engagement")
        assert len(ts) == 2

    def test_insights(self):
        self.store.add_insight({"type": "trend", "description": "Video outperforms images"})
        insights = self.store.get_insights()
        assert len(insights) == 1


class TestResearchMemoryStore:
    def setup_method(self):
        self.store = ResearchMemoryStore()

    def test_store_retrieve(self):
        self.store.store("r1", "Trending hashtags analysis")
        assert self.store.retrieve("r1") is not None

    def test_cache(self):
        self.store.cache_result("query1", {"results": [1, 2, 3]})
        cached = self.store.get_cached("query1")
        assert cached["results"] == [1, 2, 3]

    def test_sources(self):
        self.store.register_source("google_news", 0.9)
        sources = self.store.get_sources()
        assert "google_news" in sources


class TestContextMemoryStore:
    def setup_method(self):
        self.store = ContextMemoryStore()

    def test_store_retrieve(self):
        self.store.store("ctx1", {"session": "active"})
        assert self.store.retrieve("ctx1") is not None

    def test_save_load(self):
        self.store.save_context("s1", {"user_id": "u1", "platform": "twitter"})
        ctx = self.store.load_context("s1")
        assert ctx["platform"] == "twitter"

    def test_delete(self):
        self.store.save_context("s1", {"a": 1})
        assert self.store.delete_context("s1") is True


class TestWorkingMemoryStore:
    def setup_method(self):
        self.store = WorkingMemoryStore(default_ttl=1.0)

    def test_store_retrieve(self):
        self.store.store("w1", "current task")
        assert self.store.retrieve("w1") is not None

    def test_expiry(self):
        import time
        self.store.store("w1", "ephemeral")
        time.sleep(1.1)
        assert self.store.retrieve("w1") is None

    def test_cleanup(self):
        import time
        self.store.store("w1", "old")
        time.sleep(1.1)
        removed = self.store.cleanup_expired()
        assert removed >= 1


class TestGoalMemoryStore:
    def setup_method(self):
        self.store = GoalMemoryStore()

    def test_add_goal(self):
        goal = Goal("Grow followers", "Reach 10K followers")
        self.store.add_goal(goal)
        found = self.store.get_goal(str(goal.goal_id))
        assert found is not None

    def test_active_goals(self):
        g1 = Goal("Active goal")
        self.store.add_goal(g1)
        active = self.store.get_active_goals()
        assert len(active) >= 1

    def test_complete_goal(self):
        g1 = Goal("Complete me")
        self.store.add_goal(g1)
        assert self.store.complete_goal(str(g1.goal_id)) is True
        assert g1.status == "completed"


class TestMemoryRecovery:
    def setup_method(self):
        self.recovery = MemoryRecovery()

    def test_snapshot(self):
        snap = self.recovery.create_snapshot({"mem1": "data"})
        assert snap.snapshot_id > 0

    def test_get_latest(self):
        self.recovery.create_snapshot({"a": 1})
        self.recovery.create_snapshot({"b": 2})
        latest = self.recovery.get_latest_snapshot()
        assert latest.stores == {"b": 2}

    def test_restore(self):
        snap = self.recovery.create_snapshot({"data": "value"})
        restored = self.recovery.restore(snap.snapshot_id)
        assert restored == {"data": "value"}

    def test_max_snapshots(self):
        for i in range(15):
            self.recovery.create_snapshot({f"s{i}": i})
        assert self.recovery.snapshot_count() <= 10


class TestMemorySnapshotManager:
    def setup_method(self):
        self.sm = MemorySnapshotManager(interval_seconds=0.1)

    def test_take_snapshot(self):
        snap = self.sm.take_snapshot({"key": "value"})
        assert "timestamp" in snap

    def test_should_snapshot(self):
        self.sm.take_snapshot({"a": 1})
        import time
        time.sleep(0.15)
        assert self.sm.should_snapshot() is True

    def test_latest(self):
        self.sm.take_snapshot({"a": 1})
        self.sm.take_snapshot({"b": 2})
        latest = self.sm.get_latest()
        assert latest["data"] == {"b": 2}


class TestMemoryVersionManager:
    def setup_method(self):
        self.vm = MemoryVersionManager()

    def test_create_version(self):
        v = self.vm.create_version("key1", "v1")
        assert v.is_current is True

    def test_get_current(self):
        self.vm.create_version("k", "v1")
        self.vm.create_version("k", "v2")
        current = self.vm.get_current("k")
        assert current.value == "v2"

    def test_rollback(self):
        v1 = self.vm.create_version("k", "v1")
        self.vm.create_version("k", "v2")
        assert self.vm.rollback("k", v1.version_id) is True
        current = self.vm.get_current("k")
        assert current.value == "v1"

    def test_history(self):
        self.vm.create_version("k", "v1")
        self.vm.create_version("k", "v2")
        h = self.vm.get_history("k")
        assert len(h) == 2


class TestMemoryCompactor:
    def setup_method(self):
        self.compactor = MemoryCompactor()

    def test_compact(self):
        store = ConversationMemoryStore()
        store.store("old", "data")
        result = self.compactor.compact(store, max_age_seconds=0)
        assert result["removed"] >= 1

    def test_compact_by_access(self):
        store = ConversationMemoryStore()
        store.store("rare", "data")
        result = self.compactor.compact_by_access(store, min_access=1)
        assert result["removed"] >= 1


class TestMemoryIndexer:
    def setup_method(self):
        self.indexer = MemoryIndexer()

    def test_index_search(self):
        self.indexer.index_entry("doc1", "Python machine learning tutorial")
        results = self.indexer.search("machine learning")
        assert "doc1" in results

    def test_remove(self):
        self.indexer.index_entry("d1", "test content")
        self.indexer.remove_key("d1")
        results = self.indexer.search("test")
        assert "d1" not in results

    def test_stats(self):
        self.indexer.index_entry("d1", "hello world")
        s = self.indexer.stats()
        assert s["words"] >= 2


class TestMemorySearch:
    def setup_method(self):
        self.ms = MemorySearch()

    def test_register_search(self):
        conv = ConversationMemoryStore()
        conv.store("c1", "user asked about pricing")
        self.ms.register_store("conversation", conv)
        results = self.ms.search("pricing")
        assert len(results) >= 1

    def test_count_all(self):
        conv = ConversationMemoryStore()
        conv.store("k", "v")
        self.ms.register_store("conv", conv)
        counts = self.ms.count_all()
        assert counts["conv"] == 1


# ═══════════════════════════════════════════════════════════════════════
# MODULE 7: Repository Layer
# ═══════════════════════════════════════════════════════════════════════

from layers.layer13_persistence.modules.repository_layer.base_repository import BaseRepository, BaseEntity
from layers.layer13_persistence.modules.repository_layer.user_repository import UserRepository, UserEntity
from layers.layer13_persistence.modules.repository_layer.project_repository import ProjectRepository, ProjectEntity
from layers.layer13_persistence.modules.repository_layer.content_repository import ContentRepository, ContentEntity
from layers.layer13_persistence.modules.repository_layer.research_repository import ResearchRepository, ResearchEntity
from layers.layer13_persistence.modules.repository_layer.analytics_repository import AnalyticsRepository, AnalyticsEntity
from layers.layer13_persistence.modules.repository_layer.learning_repository import LearningRepository, LearningEntity
from layers.layer13_persistence.modules.repository_layer.memory_repository import MemoryRepository, MemoryEntity
from layers.layer13_persistence.modules.repository_layer.prompt_repository import PromptRepository, PromptEntity
from layers.layer13_persistence.modules.repository_layer.plugin_repository import PluginRepository, PluginEntity
from layers.layer13_persistence.modules.repository_layer.media_repository import MediaRepository, MediaEntity
from layers.layer13_persistence.modules.repository_layer.report_repository import ReportRepository, ReportEntity
from layers.layer13_persistence.modules.repository_layer.knowledge_repository import KnowledgeRepository, KnowledgeEntity
from layers.layer13_persistence.modules.repository_layer.brand_repository import BrandRepository, BrandEntity
from layers.layer13_persistence.modules.repository_layer.audit_repository import AuditRepository, AuditEntity
from layers.layer13_persistence.modules.repository_layer.goal_repository import GoalRepository, GoalEntity
from layers.layer13_persistence.modules.repository_layer.task_repository import TaskRepository, TaskEntity
from layers.layer13_persistence.modules.repository_layer.workflow_repository import WorkflowRepository, WorkflowEntity
from layers.layer13_persistence.modules.repository_layer.platform_repository import PlatformRepository, PlatformEntity


class TestBaseRepository:
    def setup_method(self):
        self.repo = BaseRepository("test")

    def test_create_get(self):
        entity = BaseEntity()
        self.repo.create(entity)
        assert self.repo.get_by_id(entity.id) is not None

    def test_get_all(self):
        self.repo.create(BaseEntity())
        self.repo.create(BaseEntity())
        assert len(self.repo.get_all()) == 2

    def test_update(self):
        entity = BaseEntity()
        self.repo.create(entity)
        self.repo.update(entity.id, {"metadata": {"updated": True}})
        found = self.repo.get_by_id(entity.id)
        assert found is not None

    def test_delete(self):
        entity = BaseEntity()
        self.repo.create(entity)
        assert self.repo.delete(entity.id) is True
        assert self.repo.exists(entity.id) is False

    def test_find(self):
        e1 = BaseEntity()
        self.repo.create(e1)
        results = self.repo.find(id=e1.id)
        assert len(results) == 1

    def test_count(self):
        self.repo.create(BaseEntity())
        assert self.repo.count() == 1

    def test_clear(self):
        self.repo.create(BaseEntity())
        count = self.repo.clear()
        assert count == 1
        assert self.repo.count() == 0


class TestUserRepository:
    def setup_method(self):
        self.repo = UserRepository()

    def test_create_find(self):
        user = UserEntity("alice", "alice@example.com")
        self.repo.create(user)
        assert self.repo.find_by_email("alice@example.com") is not None

    def test_find_by_username(self):
        self.repo.create(UserEntity("bob", "bob@test.com"))
        assert self.repo.find_by_username("bob") is not None

    def test_find_by_role(self):
        self.repo.create(UserEntity("admin", "a@test.com", "admin"))
        self.repo.create(UserEntity("user", "u@test.com", "user"))
        assert len(self.repo.find_by_role("admin")) == 1


class TestProjectRepository:
    def setup_method(self):
        self.repo = ProjectRepository()

    def test_create_find(self):
        p = ProjectEntity("AI Agent", "Universal AI content agent", owner_id=1)
        self.repo.create(p)
        assert len(self.repo.find_by_owner(1)) == 1

    def test_by_status(self):
        e = ProjectEntity("A")
        e.status = "active"
        self.repo.create(e)
        assert len(self.repo.find_by_status("active")) == 1


class TestContentRepository:
    def setup_method(self):
        self.repo = ContentRepository()

    def test_create_find(self):
        c = ContentEntity("My Post", "Content body", "post")
        c.platform = "twitter"
        self.repo.create(c)
        assert len(self.repo.find_by_platform("twitter")) == 1

    def test_published(self):
        c = ContentEntity("Published Post")
        c.status = "published"
        self.repo.create(c)
        assert len(self.repo.find_published()) == 1


class TestResearchRepository:
    def setup_method(self):
        self.repo = ResearchRepository()

    def test_create_find(self):
        r = ResearchEntity("AI trends 2024", source="google")
        self.repo.create(r)
        assert len(self.repo.find_by_source("google")) == 1

    def test_high_confidence(self):
        r1 = ResearchEntity("q1", source="a")
        r1.confidence = 0.9
        r2 = ResearchEntity("q2", source="b")
        r2.confidence = 0.3
        self.repo.create(r1)
        self.repo.create(r2)
        assert len(self.repo.find_high_confidence(0.7)) == 1


class TestAnalyticsRepository:
    def setup_method(self):
        self.repo = AnalyticsRepository()

    def test_create_find(self):
        a = AnalyticsEntity("engagement", 0.85, "twitter")
        self.repo.create(a)
        assert len(self.repo.find_by_metric("engagement")) == 1

    def test_total(self):
        self.repo.create(AnalyticsEntity("likes", 100, "fb"))
        self.repo.create(AnalyticsEntity("likes", 200, "fb"))
        assert self.repo.get_metric_total("likes") == 300


class TestLearningRepository:
    def setup_method(self):
        self.repo = LearningRepository()

    def test_create_find(self):
        l = LearningEntity("writing", "Short captions work best", "high")
        self.repo.create(l)
        assert len(self.repo.find_by_type("writing")) == 1

    def test_applied_unapplied(self):
        l1 = LearningEntity("a", "d1")
        l1.applied = True
        l2 = LearningEntity("b", "d2")
        self.repo.create(l1)
        self.repo.create(l2)
        assert len(self.repo.find_applied()) == 1
        assert len(self.repo.find_unapplied()) == 1


class TestMemoryRepository:
    def setup_method(self):
        self.repo = MemoryRepository()

    def test_create_find(self):
        m = MemoryEntity("semantic", "python_fact", "Python is popular")
        self.repo.create(m)
        assert len(self.repo.find_by_type("semantic")) == 1

    def test_by_key(self):
        self.repo.create(MemoryEntity("m", "k1", "v1"))
        assert len(self.repo.find_by_key("k1")) == 1


class TestPromptRepository:
    def setup_method(self):
        self.repo = PromptRepository()

    def test_create_find(self):
        p = PromptEntity("tweet_prompt", "Write a tweet about {topic}")
        self.repo.create(p)
        assert len(self.repo.find_by_name("tweet_prompt")) == 1

    def test_best(self):
        p1 = PromptEntity("good", "prompt1")
        p1.performance_score = 0.9
        p2 = PromptEntity("bad", "prompt2")
        p2.performance_score = 0.3
        self.repo.create(p1)
        self.repo.create(p2)
        best = self.repo.find_best(1)
        assert best[0].name == "good"


class TestPluginRepository:
    def setup_method(self):
        self.repo = PluginRepository()

    def test_create_find(self):
        p = PluginEntity("facebook", "2.0.0", "facebook")
        self.repo.create(p)
        assert len(self.repo.find_by_platform("facebook")) == 1

    def test_enabled(self):
        p1 = PluginEntity("a")
        p1.enabled = True
        p2 = PluginEntity("b")
        p2.enabled = False
        self.repo.create(p1)
        self.repo.create(p2)
        assert len(self.repo.find_enabled()) == 1


class TestMediaRepository:
    def setup_method(self):
        self.repo = MediaRepository()

    def test_create_find(self):
        m = MediaEntity("photo.jpg", "image")
        m.size_bytes = 1024
        self.repo.create(m)
        assert len(self.repo.find_by_type("image")) == 1

    def test_total_size(self):
        m1 = MediaEntity("a.jpg", "image")
        m1.size_bytes = 100
        m2 = MediaEntity("b.mp4", "video")
        m2.size_bytes = 500
        self.repo.create(m1)
        self.repo.create(m2)
        assert self.repo.total_size() == 600


class TestReportRepository:
    def setup_method(self):
        self.repo = ReportRepository()

    def test_create_find(self):
        r = ReportEntity("weekly", "Week 1 Report")
        self.repo.create(r)
        assert len(self.repo.find_by_type("weekly")) == 1


class TestKnowledgeRepository:
    def setup_method(self):
        self.repo = KnowledgeRepository()

    def test_create_find(self):
        k = KnowledgeEntity("AI trends", "Content about AI", "technology")
        self.repo.create(k)
        assert len(self.repo.find_by_category("technology")) == 1

    def test_by_topic(self):
        self.repo.create(KnowledgeEntity("Python", "programming language"))
        assert len(self.repo.find_by_topic("Python")) == 1


class TestBrandRepository:
    def setup_method(self):
        self.repo = BrandRepository()

    def test_create_find(self):
        b = BrandEntity("MyBrand", "tone", "Professional tone")
        self.repo.create(b)
        assert len(self.repo.find_by_type("tone")) == 1

    def test_by_platform(self):
        b = BrandEntity("B", "style", "Casual")
        b.platform = "instagram"
        self.repo.create(b)
        assert len(self.repo.find_by_platform("instagram")) == 1


class TestAuditRepository:
    def setup_method(self):
        self.repo = AuditRepository()

    def test_create_find(self):
        a = AuditEntity("create", "content", 42)
        a.user_id = 1
        self.repo.create(a)
        assert len(self.repo.find_by_action("create")) == 1

    def test_by_user(self):
        a1 = AuditEntity("update")
        a1.user_id = 1
        self.repo.create(a1)
        a2 = AuditEntity("delete")
        a2.user_id = 2
        self.repo.create(a2)
        assert len(self.repo.find_by_user(1)) == 1


class TestGoalRepository:
    def setup_method(self):
        self.repo = GoalRepository()

    def test_create_find(self):
        g = GoalEntity("Grow followers", priority=8)
        self.repo.create(g)
        assert len(self.repo.find_active()) == 1

    def test_completed(self):
        g = GoalEntity("Done")
        g.status = "completed"
        self.repo.create(g)
        assert len(self.repo.find_completed()) == 1

    def test_by_priority(self):
        self.repo.create(GoalEntity("High", priority=9))
        self.repo.create(GoalEntity("Low", priority=2))
        assert len(self.repo.find_by_priority(5)) == 1


class TestTaskRepository:
    def setup_method(self):
        self.repo = TaskRepository()

    def test_create_find(self):
        t = TaskEntity("Write post", assigned_to=1)
        self.repo.create(t)
        assert len(self.repo.find_pending()) == 1

    def test_by_assignee(self):
        self.repo.create(TaskEntity("A", assigned_to=1))
        self.repo.create(TaskEntity("B", assigned_to=2))
        assert len(self.repo.find_by_assignee(1)) == 1


class TestWorkflowRepository:
    def setup_method(self):
        self.repo = WorkflowRepository()

    def test_create_find(self):
        w = WorkflowEntity("Content Pipeline", ["research", "write", "publish"])
        w.status = "running"
        self.repo.create(w)
        assert len(self.repo.find_running()) == 1

    def test_completed(self):
        w = WorkflowEntity("Done")
        w.status = "completed"
        self.repo.create(w)
        assert len(self.repo.find_completed()) == 1


class TestPlatformRepository:
    def setup_method(self):
        self.repo = PlatformRepository()

    def test_create_find(self):
        p = PlatformEntity("Facebook", "social")
        self.repo.create(p)
        assert len(self.repo.find_by_type("social")) == 1

    def test_enabled(self):
        p1 = PlatformEntity("Twitter", "social")
        p1.enabled = True
        p2 = PlatformEntity("Old", "social")
        p2.enabled = False
        self.repo.create(p1)
        self.repo.create(p2)
        assert len(self.repo.find_enabled()) == 1
