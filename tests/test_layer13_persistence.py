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
