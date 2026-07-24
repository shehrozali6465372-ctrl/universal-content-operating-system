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
        assert self.rc.delete("key1") >= 1
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

    def _auto_id(self, counter=[0]):
        counter[0] += 1
        return f"rec_{counter[0]}"

    def test_upsert(self):
        vec = [0.1] * 128
        record = self.vs.upsert(self._auto_id(), vec, {"source": "test"})
        assert record.record_id is not None
        assert record.record_id != ""

    def test_search(self):
        vec1 = [1.0] + [0.0] * 127
        vec2 = [0.0] + [1.0] * 127
        self.vs.upsert("a1", vec1, {"label": "a"})
        self.vs.upsert("b1", vec2, {"label": "b"})
        results = self.vs.search(vec1, top_k=1)
        assert len(results) == 1
        assert results[0][0].metadata["label"] == "a"

    def test_search_with_filter(self):
        vec = [0.5] * 128
        self.vs.upsert("f1", vec, {"type": "a"})
        self.vs.upsert("f2", vec, {"type": "b"})
        results = self.vs.search(vec, top_k=10,
                                 filter_fn=lambda rec: rec.metadata.get("type") == "a")
        assert all(r.metadata["type"] == "a" for r, _ in results)

    def test_delete(self):
        record = self.vs.upsert("d1", [0.1] * 128)
        assert self.vs.delete(record.record_id) is True

    def test_count(self):
        self.vs.upsert("c1", [0.1] * 128)
        self.vs.upsert("c2", [0.2] * 128)
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


# ═══════════════════════════════════════════════════════════════════════
# MODULE 8: Event Store
# ═══════════════════════════════════════════════════════════════════════

from layers.layer13_persistence.modules.event_store.event import Event
from layers.layer13_persistence.modules.event_store.event_store import EventStore
from layers.layer13_persistence.modules.event_store.event_stream import EventStream
from layers.layer13_persistence.modules.event_store.snapshot_manager import SnapshotManager
from layers.layer13_persistence.modules.event_store.replay_engine import ReplayEngine
from layers.layer13_persistence.modules.event_store.event_archive import EventArchive
from layers.layer13_persistence.modules.event_store.event_compression import EventCompressor
from layers.layer13_persistence.modules.event_store.event_replication import EventReplicator
from layers.layer13_persistence.modules.event_store.event_versioning import EventVersionManager
from layers.layer13_persistence.modules.event_store.event_search import EventSearcher
from layers.layer13_persistence.modules.event_store.event_recovery import EventRecovery
from layers.layer13_persistence.modules.event_store.event_metrics import EventMetrics
from layers.layer13_persistence.modules.event_store.event_report import EventReport


class TestEvent:
    def test_create(self):
        e = Event("PostCreated", "agg_1", {"title": "Hello"})
        assert e.event_type == "PostCreated"
        assert e.aggregate_id == "agg_1"

    def test_to_dict(self):
        e = Event("Test", "a1", {"k": "v"})
        d = e.to_dict()
        assert "type" in d
        assert d["data"]["k"] == "v"


class TestEventStore:
    def setup_method(self):
        self.es = EventStore()

    def test_append(self):
        e = Event("Created", "agg1", {"name": "test"})
        result = self.es.append(e)
        assert result.version == 1

    def test_get_events(self):
        self.es.append(Event("Created", "agg1"))
        self.es.append(Event("Updated", "agg1"))
        events = self.es.get_events("agg1")
        assert len(events) == 2

    def test_versioning(self):
        self.es.append(Event("A", "agg1"))
        self.es.append(Event("B", "agg1"))
        assert self.es.get_version("agg1") == 2

    def test_get_from_version(self):
        self.es.append(Event("A", "agg1"))
        self.es.append(Event("B", "agg1"))
        events = self.es.get_events_from("agg1", from_version=1)
        assert len(events) == 1

    def test_global_events(self):
        self.es.append(Event("A", "agg1"))
        self.es.append(Event("B", "agg2"))
        assert len(self.es.get_global_events()) == 2

    def test_by_type(self):
        self.es.append(Event("Created", "a1"))
        self.es.append(Event("Updated", "a1"))
        assert len(self.es.get_events_by_type("Created")) == 1

    def test_stats(self):
        self.es.append(Event("A", "a1"))
        s = self.es.stats()
        assert s["total_events"] == 1


class TestEventStream:
    def setup_method(self):
        self.stream = EventStream()

    def test_publish_subscribe(self):
        received = []
        self.stream.subscribe("test", lambda e: received.append(e))
        self.stream.publish(Event("test", "a1"))
        assert len(received) == 1

    def test_wildcard(self):
        received = []
        self.stream.subscribe("*", lambda e: received.append(e))
        self.stream.publish(Event("any", "a1"))
        assert len(received) == 1

    def test_history(self):
        self.stream.publish(Event("A", "a1"))
        h = self.stream.get_history()
        assert len(h) == 1

    def test_clear(self):
        self.stream.publish(Event("A", "a1"))
        count = self.stream.clear_history()
        assert count == 1


class TestSnapshotManager:
    def setup_method(self):
        self.sm = SnapshotManager(snapshot_interval=5)

    def test_save_get(self):
        snap = self.sm.save("agg1", 10, {"count": 5})
        found = self.sm.get("agg1")
        assert found.version == 10

    def test_should_snapshot(self):
        self.sm.save("agg1", 1, {})
        assert self.sm.should_snapshot("agg1", 6) is True
        assert self.sm.should_snapshot("agg1", 3) is False

    def test_delete(self):
        self.sm.save("agg1", 1, {})
        assert self.sm.delete("agg1") is True


class TestReplayEngine:
    def setup_method(self):
        self.engine = ReplayEngine()

    def test_replay(self):
        self.engine.register_handler("Created", lambda s, e: {**s, "created": True})
        self.engine.register_handler("Updated", lambda s, e: {**s, "updated": True})
        events = [Event("Created", "a1"), Event("Updated", "a1")]
        state = self.engine.replay(events)
        assert state["created"] is True
        assert state["updated"] is True

    def test_replay_aggregate(self):
        self.engine.register_handler("Test", lambda s, e: {**s, "done": True})
        events = [Event("Test", "a1"), Event("Test", "a2")]
        state = self.engine.replay_aggregate("a1", events)
        assert state["done"] is True


class TestEventArchive:
    def setup_method(self):
        self.archive = EventArchive(max_age_days=0)

    def test_archive(self):
        import time
        e = Event("Old", "a1")
        e.timestamp = time.time() - 100000
        archived = self.archive.archive([e])
        assert len(archived) == 1

    def test_archived_count(self):
        import time
        e = Event("Old", "a1")
        e.timestamp = time.time() - 100000
        self.archive.archive([e])
        assert self.archive.archived_count() == 1


class TestEventCompressor:
    def setup_method(self):
        self.comp = EventCompressor()

    def test_compress(self):
        events = [Event("A", "a1", {"k": "v"}), Event("B", "a2")]
        compressed = self.comp.compress_events(events)
        assert isinstance(compressed, bytes)

    def test_ratio(self):
        original = b"hello world " * 100
        compressed = self.comp.compress_events([])
        ratio = self.comp.get_compression_ratio(original, original[:50])
        assert ratio < 1.0


class TestEventReplicator:
    def setup_method(self):
        self.rep = EventReplicator()

    def test_register_replicate(self):
        self.rep.register_node("node1")
        self.rep.register_node("node2")
        e = Event("Test", "a1")
        count = self.rep.replicate(e)
        assert count == 2

    def test_replicate_specific(self):
        self.rep.register_node("node1")
        self.rep.register_node("node2")
        count = self.rep.replicate(Event("T", "a1"), ["node1"])
        assert count == 1


class TestEventVersionManager:
    def setup_method(self):
        self.vm = EventVersionManager()

    def test_register(self):
        self.vm.register("PostCreated", 1, {"title": "string"})
        latest = self.vm.get_latest("PostCreated")
        assert latest.version == 1

    def test_multiple_versions(self):
        self.vm.register("E", 1)
        self.vm.register("E", 2)
        assert self.vm.get_latest("E").version == 2

    def test_stats(self):
        self.vm.register("A", 1)
        self.vm.register("B", 1)
        s = self.vm.stats()
        assert s["types"] == 2


class TestEventSearcher:
    def setup_method(self):
        self.searcher = EventSearcher()

    def test_index_search(self):
        e1 = Event("PostCreated", "a1", {"title": "AI trends"})
        e2 = Event("PostUpdated", "a2", {"title": "Marketing tips"})
        self.searcher.index([e1, e2])
        results = self.searcher.search("AI", [e1, e2])
        assert len(results) == 1


class TestEventRecovery:
    def setup_method(self):
        self.recovery = EventRecovery()

    def test_recover(self):
        events = [Event("A", "a1"), Event("B", "a2"), Event("C", "a3")]
        events[0].version = 1
        events[1].version = 2
        events[2].version = 3
        recovered = self.recovery.recover_from_store(events, from_version=2)
        assert len(recovered) == 2

    def test_log(self):
        self.recovery.recover_from_store([Event("A", "a1")])
        log = self.recovery.get_recovery_log()
        assert len(log) == 1


class TestEventMetrics:
    def setup_method(self):
        self.metrics = EventMetrics()

    def test_record(self):
        self.metrics.record_append("PostCreated")
        self.metrics.record_read(5)
        d = self.metrics.to_dict()
        assert d["appended"] == 1

    def test_by_type(self):
        self.metrics.record_append("A")
        self.metrics.record_append("A")
        self.metrics.record_append("B")
        d = self.metrics.to_dict()
        assert d["by_type"]["A"] == 2


class TestEventReport:
    def setup_method(self):
        self.report = EventReport()

    def test_generate(self):
        r = self.report.generate({"appended": 10}, {"total": 100})
        assert "metrics" in r

    def test_history(self):
        self.report.generate({}, {})
        h = self.report.get_history()
        assert len(h) == 1


# ═══════════════════════════════════════════════════════════════════════
# MODULE 9: Backup & DR
# ═══════════════════════════════════════════════════════════════════════

from layers.layer13_persistence.modules.backup_dr.backup_scheduler import BackupScheduler, BackupSchedule
from layers.layer13_persistence.modules.backup_dr.incremental_backup import IncrementalBackupManager
from layers.layer13_persistence.modules.backup_dr.full_backup import FullBackupManager
from layers.layer13_persistence.modules.backup_dr.snapshot_engine import SnapshotEngine
from layers.layer13_persistence.modules.backup_dr.recovery_engine import RecoveryEngine
from layers.layer13_persistence.modules.backup_dr.replication_engine import ReplicationEngine
from layers.layer13_persistence.modules.backup_dr.failover_manager import FailoverManager
from layers.layer13_persistence.modules.backup_dr.disaster_recovery import DisasterRecoveryManager
from layers.layer13_persistence.modules.backup_dr.backup_validator import BackupValidator
from layers.layer13_persistence.modules.backup_dr.backup_encryption import BackupEncryptor
from layers.layer13_persistence.modules.backup_dr.recovery_testing import RecoveryTestManager
from layers.layer13_persistence.modules.backup_dr.recovery_metrics import RecoveryMetrics


class TestBackupScheduler:
    def setup_method(self):
        self.bs = BackupScheduler()

    def test_add_schedule(self):
        s = BackupSchedule("daily_backup", "full", 86400)
        self.bs.add_schedule(s)
        assert len(self.bs.list_schedules()) == 1

    def test_get_due(self):
        s = BackupSchedule("due", "full", 0)
        s.next_run = 0
        self.bs.add_schedule(s)
        assert len(self.bs.get_due_schedules()) == 1

    def test_mark_completed(self):
        s = BackupSchedule("test", "full", 100)
        self.bs.add_schedule(s)
        self.bs.mark_completed(s.schedule_id)
        assert len(self.bs._history) == 1


class TestIncrementalBackupManager:
    def setup_method(self):
        self.ibm = IncrementalBackupManager()

    def test_create(self):
        b = self.ibm.create(changes=[{"table": "users", "op": "insert"}])
        assert b.status == "completed"

    def test_chain(self):
        b1 = self.ibm.create()
        b2 = self.ibm.create(parent_id=b1.backup_id)
        chain = self.ibm.get_chain(b2.backup_id)
        assert len(chain) == 2


class TestFullBackupManager:
    def setup_method(self):
        self.fbm = FullBackupManager(max_backups=5)

    def test_create(self):
        b = self.fbm.create("weekly", ["users", "posts"])
        assert len(self.fbm.get_all()) == 1

    def test_max_limit(self):
        for i in range(10):
            self.fbm.create(f"backup_{i}")
        assert len(self.fbm.get_all()) <= 5

    def test_latest(self):
        self.fbm.create("first")
        self.fbm.create("second")
        assert self.fbm.get_latest().name == "second"


class TestSnapshotEngine:
    def setup_method(self):
        self.se = SnapshotEngine()

    def test_take_snapshot(self):
        snap = self.se.take_snapshot({"users": 100, "posts": 500})
        assert snap.snapshot_id > 0

    def test_restore(self):
        snap = self.se.take_snapshot({"data": "value"})
        state = self.se.restore(snap.snapshot_id)
        assert state["data"] == "value"

    def test_latest(self):
        self.se.take_snapshot({"a": 1})
        self.se.take_snapshot({"b": 2})
        latest = self.se.get_latest()
        assert latest.state["b"] == 2


class TestRecoveryEngine:
    def setup_method(self):
        self.re = RecoveryEngine()

    def test_create_execute(self):
        plan = self.re.create_plan(["check_db", "restore_backup", "verify"])
        assert self.re.execute(plan.plan_id) is True

    def test_get_executed(self):
        plan = self.re.create_plan(["step1"])
        self.re.execute(plan.plan_id)
        assert len(self.re.get_executed()) == 1


class TestReplicationEngine:
    def setup_method(self):
        self.re = ReplicationEngine()

    def test_add_replicate(self):
        n1 = self.re.add_node("node1.local")
        n2 = self.re.add_node("node2.local")
        count = self.re.replicate({"data": 1})
        assert count == 2

    def test_is_healthy(self):
        self.re.add_node("n1")
        assert self.re.is_healthy() is True

    def test_remove(self):
        n = self.re.add_node("n1")
        assert self.re.remove_node(n.node_id) is True


class TestFailoverManager:
    def setup_method(self):
        self.fm = FailoverManager()

    def test_set_active(self):
        self.fm.set_active("node1")
        assert self.fm.get_active_node() == "node1"

    def test_failover(self):
        self.fm.set_active("node1")
        event = self.fm.trigger_failover("node1", "node2", "node1 down")
        assert self.fm.get_active_node() == "node2"
        assert len(self.fm.get_events()) == 1


class TestDisasterRecoveryManager:
    def setup_method(self):
        self.drm = DisasterRecoveryManager()

    def test_create_plan(self):
        plan = self.drm.create_plan("Primary DR", rto=1800, rpo=300)
        assert plan.name == "Primary DR"

    def test_drill(self):
        plan = self.drm.create_plan("Test DR")
        assert self.drm.run_drill(plan.plan_id) is True

    def test_stats(self):
        self.drm.create_plan("DR1")
        s = self.drm.stats()
        assert s["plans"] == 1


class TestBackupValidator:
    def setup_method(self):
        self.bv = BackupValidator()

    def test_valid(self):
        result = self.bv.validate(1, 1000, 1000, True)
        assert result["valid"] is True

    def test_invalid(self):
        result = self.bv.validate(1, 1000, 500, True)
        assert result["valid"] is False


class TestBackupEncryptor:
    def setup_method(self):
        self.be = BackupEncryptor()

    def test_encrypt_decrypt(self):
        original = b"backup data"
        encrypted = self.be.encrypt(original, "key123")
        decrypted = self.be.decrypt(encrypted, "key123")
        assert decrypted == original

    def test_verify(self):
        original = b"test"
        encrypted = self.be.encrypt(original, "key")
        assert self.be.verify(original, encrypted, "key") is True


class TestRecoveryTestManager:
    def setup_method(self):
        self.rtm = RecoveryTestManager()

    def test_run(self):
        test = self.rtm.run_test(1, success=True, duration_ms=500)
        assert test.success is True

    def test_success_rate(self):
        self.rtm.run_test(1, True)
        self.rtm.run_test(1, False)
        assert self.rtm.success_rate() == 0.5


class TestRecoveryMetrics:
    def setup_method(self):
        self.rm = RecoveryMetrics()

    def test_record(self):
        self.rm.record_backup(True)
        self.rm.record_backup(False)
        self.rm.record_restore(True)
        d = self.rm.to_dict()
        assert d["backups"] == 2


# ═══════════════════════════════════════════════════════════════════════
# MODULE 10: Universal Orchestrator
# ═══════════════════════════════════════════════════════════════════════

from layers.layer13_persistence.modules.universal_orchestrator.storage_router import StorageRouter
from layers.layer13_persistence.modules.universal_orchestrator.persistence_orchestrator import PersistenceOrchestrator
from layers.layer13_persistence.modules.universal_orchestrator.transaction_coordinator import TransactionCoordinator
from layers.layer13_persistence.modules.universal_orchestrator.cache_coordinator import CacheCoordinator
from layers.layer13_persistence.modules.universal_orchestrator.replication_coordinator import ReplicationCoordinator
from layers.layer13_persistence.modules.universal_orchestrator.recovery_coordinator import RecoveryCoordinator
from layers.layer13_persistence.modules.universal_orchestrator.health_coordinator import HealthCoordinator
from layers.layer13_persistence.modules.universal_orchestrator.backup_coordinator import BackupCoordinator
from layers.layer13_persistence.modules.universal_orchestrator.migration_coordinator import MigrationCoordinator
from layers.layer13_persistence.modules.universal_orchestrator.optimization_coordinator import OptimizationCoordinator
from layers.layer13_persistence.modules.universal_orchestrator.consistency_checker import ConsistencyChecker
from layers.layer13_persistence.modules.universal_orchestrator.garbage_collector import GarbageCollector
from layers.layer13_persistence.modules.universal_orchestrator.performance_tuner import PerformanceTuner
from layers.layer13_persistence.modules.universal_orchestrator.cost_optimizer import CostOptimizer
from layers.layer13_persistence.modules.universal_orchestrator.storage_balancer import StorageBalancer
from layers.layer13_persistence.modules.universal_orchestrator.auto_scaler import AutoScaler
from layers.layer13_persistence.modules.universal_orchestrator.storage_advisor import StorageAdvisor
from layers.layer13_persistence.modules.universal_orchestrator.persistence_ai import PersistenceAI


class TestStorageRouter:
    def setup_method(self):
        self.sr = StorageRouter()

    def test_route(self):
        self.sr.route("users", "postgresql")
        assert self.sr.get_backend("users") == "postgresql"

    def test_default(self):
        assert self.sr.get_backend("unknown") == "memory"

    def test_register(self):
        self.sr.register_backend("pg", {"type": "sql"})
        self.sr.route("users", "pg")
        assert self.sr.get_backend_instance("users") is not None


class TestPersistenceOrchestrator:
    def setup_method(self):
        self.po = PersistenceOrchestrator()

    def test_initialize(self):
        assert self.po.initialize() is True
        assert self.po.is_initialized() is True

    def test_shutdown(self):
        self.po.initialize()
        assert self.po.shutdown() is True

    def test_route(self):
        self.po.route_data("users", "postgres")
        assert self.po.get_router().get_backend("users") == "postgres"


class TestTransactionCoordinator:
    def setup_method(self):
        self.tc = TransactionCoordinator()

    def test_begin_commit(self):
        tx = self.tc.begin()
        self.tc.add_operation(tx.tx_id, "db", "insert", {"user": "alice"})
        assert self.tc.commit(tx.tx_id) is True

    def test_rollback(self):
        tx = self.tc.begin()
        assert self.tc.rollback(tx.tx_id) is True
        assert tx.status == "rolled_back"

    def test_active(self):
        self.tc.begin()
        self.tc.begin()
        assert len(self.tc.get_active()) == 2


class TestCacheCoordinator:
    def setup_method(self):
        self.cc = CacheCoordinator()

    def test_invalidate(self):
        self.cc.invalidate("cache1", "user:*")
        assert len(self.cc.get_pending()) == 1

    def test_invalidate_all(self):
        self.cc.invalidate("c", "k")
        count = self.cc.invalidate_all()
        assert count == 1

    def test_patterns(self):
        self.cc.invalidate("c", "a:*")
        self.cc.invalidate("c", "b:*")
        assert len(self.cc.get_patterns("c")) == 2


class TestReplicationCoordinator:
    def setup_method(self):
        self.rc = ReplicationCoordinator()

    def test_register_replicate(self):
        self.rc.register_store("users", ["replica1", "replica2"])
        count = self.rc.replicate("users")
        assert count == 2

    def test_is_replicated(self):
        self.rc.register_store("s1", ["r1"])
        assert self.rc.is_replicated("s1") is True


class TestRecoveryCoordinator:
    def setup_method(self):
        self.rec = RecoveryCoordinator()

    def test_register_execute(self):
        self.rec.register_plan("db1", ["check", "restore", "verify"])
        assert self.rec.execute_recovery("db1") is True


class TestHealthCoordinator:
    def setup_method(self):
        self.hc = HealthCoordinator()

    def test_check(self):
        self.hc.check("db1", True, 5.0)
        assert self.hc.is_healthy() is True

    def test_degraded(self):
        self.hc.check("db1", True)
        self.hc.check("db2", False)
        assert self.hc.is_healthy() is False


class TestBackupCoordinator:
    def setup_method(self):
        self.bc = BackupCoordinator()

    def test_schedule_trigger(self):
        self.bc.schedule_backup("db", 3600)
        assert self.bc.trigger_backup("db") is True


class TestMigrationCoordinator:
    def setup_method(self):
        self.mc = MigrationCoordinator()

    def test_register_apply(self):
        self.mc.register_migration("db", "1.0", "CREATE TABLE t")
        count = self.mc.apply_pending("db")
        assert count == 1

    def test_pending(self):
        self.mc.register_migration("db", "1.0", "SQL")
        self.mc.register_migration("db", "2.0", "SQL")
        applied = self.mc.apply_pending("db")
        assert applied == 2
        assert len(self.mc.get_pending("db")) == 0


class TestOptimizationCoordinator:
    def setup_method(self):
        self.oc = OptimizationCoordinator()

    def test_suggest_apply(self):
        self.oc.suggest("db", "add index", "high")
        assert self.oc.apply(0) is True
        assert len(self.oc.get_applied()) == 1


class TestConsistencyChecker:
    def setup_method(self):
        self.cc = ConsistencyChecker()

    def test_check(self):
        result = self.cc.check({"db1": "data", "db2": "data"})
        assert result["consistent"] is True


class TestGarbageCollector:
    def setup_method(self):
        self.gc = GarbageCollector()

    def test_collect(self):
        self.gc.collect("db1", 100)
        assert self.gc.get_stats("db1") == 100


class TestPerformanceTuner:
    def setup_method(self):
        self.pt = PerformanceTuner()

    def test_analyze(self):
        result = self.pt.analyze("db1", {"latency_ms": 200})
        assert result["suggestion"] == "add_index"


class TestCostOptimizer:
    def setup_method(self):
        self.co = CostOptimizer(budget=100.0)

    def test_record(self):
        self.co.record_cost("db", 50.0)
        assert self.co.get_total_cost() == 50.0

    def test_budget(self):
        self.co.record_cost("db", 100.0)
        assert self.co.get_remaining_budget() == 0.0


class TestStorageBalancer:
    def setup_method(self):
        self.sb = StorageBalancer()

    def test_distribute(self):
        self.sb.register("s1", 100)
        self.sb.register("s2", 100)
        target = self.sb.distribute("users", {"data": 1})
        assert target in ("s1", "s2")


class TestAutoScaler:
    def setup_method(self):
        self.as_ = AutoScaler(min_capacity=1, max_capacity=10)

    def test_scale_up(self):
        assert self.as_.should_scale_up(0.9) is True
        self.as_.scale_up(2)
        assert self.as_.get_capacity() == 3

    def test_scale_down(self):
        self.as_.scale_up(5)
        assert self.as_.should_scale_down(0.1) is True
        self.as_.scale_down(3)
        assert self.as_.get_capacity() == 3


class TestStorageAdvisor:
    def setup_method(self):
        self.sa = StorageAdvisor()

    def test_analyze(self):
        recs = self.sa.analyze({"storage_used_gb": 200, "cache_hit_rate": 0.3,
                                 "query_latency_ms": 300})
        assert len(recs) >= 2


class TestPersistenceAI:
    def setup_method(self):
        self.ai = PersistenceAI()

    def test_patterns(self):
        insight = self.ai.analyze_patterns({"write_heavy": True})
        assert "write_heavy" in insight["patterns"]

    def test_growth(self):
        pred = self.ai.predict_growth(100, [50, 75, 100])
        assert pred["predicted_next"] > 100


# ═══════════════════════════════════════════════════════════════════════
# MODULE 1 EXPANSION: Kernel extras
# ═══════════════════════════════════════════════════════════════════════

from layers.layer13_persistence.modules.persistence_kernel.persistence_state import PersistenceState
from layers.layer13_persistence.modules.persistence_kernel.persistence_capabilities import PersistenceCapabilities
from layers.layer13_persistence.modules.persistence_kernel.persistence_registry import PersistenceRegistry
from layers.layer13_persistence.modules.persistence_kernel.persistence_clock import PersistenceClock
from layers.layer13_persistence.modules.persistence_kernel.persistence_telemetry import PersistenceTelemetry
from layers.layer13_persistence.modules.persistence_kernel.persistence_monitor import PersistenceMonitor
from layers.layer13_persistence.modules.persistence_kernel.persistence_hooks import PersistenceHooks
from layers.layer13_persistence.modules.persistence_kernel.persistence_validator import PersistenceValidator


class TestPersistenceState:
    def setup_method(self):
        self.ps = PersistenceState()

    def test_initial_state(self):
        assert self.ps.get_state() == "uninitialized"

    def test_set_state(self):
        assert self.ps.set_state("ready") is True
        assert self.ps.get_state() == "ready"

    def test_invalid_state(self):
        assert self.ps.set_state("bogus") is False

    def test_sub_state(self):
        self.ps.set_sub_state("sql", "healthy")
        assert self.ps.get_sub_state("sql") == "healthy"

    def test_is_ready(self):
        self.ps.set_state("ready")
        assert self.ps.is_ready() is True

    def test_transitions(self):
        self.ps.set_state("initializing")
        self.ps.set_state("ready")
        assert len(self.ps.get_transitions()) == 2


class TestPersistenceCapabilities:
    def setup_method(self):
        self.pc = PersistenceCapabilities()

    def test_register(self):
        self.pc.register("sql", "SQL support", ["postgresql", "mysql"])
        assert self.pc.has("sql") is True

    def test_enable_disable(self):
        self.pc.register("redis")
        self.pc.disable("redis")
        assert self.pc.has("redis") is False
        self.pc.enable("redis")
        assert self.pc.has("redis") is True

    def test_features(self):
        self.pc.register("vector", features=["qdrant", "milvus"])
        assert "qdrant" in self.pc.get_features("vector")


class TestPersistenceRegistry:
    def setup_method(self):
        self.pr = PersistenceRegistry()

    def test_register_get(self):
        self.pr.register("sql", {"type": "database"}, "storage")
        assert self.pr.get("sql") is not None
        assert self.pr.has("sql") is True

    def test_unregister(self):
        self.pr.register("sql", {})
        assert self.pr.unregister("sql") is True
        assert self.pr.has("sql") is False

    def test_count(self):
        self.pr.register("a", {})
        self.pr.register("b", {})
        assert self.pr.count() == 2

    def test_stats(self):
        self.pr.register("a", {}, "storage")
        s = self.pr.stats()
        assert s["total"] == 1


class TestPersistenceClock:
    def setup_method(self):
        self.pc = PersistenceClock()

    def test_tick(self):
        t1 = self.pc.tick()
        t2 = self.pc.tick()
        assert t2 > t1

    def test_update_if_greater(self):
        self.pc.tick()
        assert self.pc.update_if_greater(100) is True
        assert self.pc.now() == 100

    def test_reset(self):
        self.pc.tick()
        self.pc.reset()
        assert self.pc.now() == 0


class TestPersistenceTelemetry:
    def setup_method(self):
        self.pt = PersistenceTelemetry()

    def test_span(self):
        span = self.pt.start_span("query")
        span.finish()
        assert len(self.pt.get_spans()) == 1

    def test_increment(self):
        self.pt.increment("queries")
        self.pt.increment("queries")
        assert self.pt.get_counters()["queries"] == 2


class TestPersistenceMonitor:
    def setup_method(self):
        self.pm = PersistenceMonitor()

    def test_record(self):
        self.pm.set_threshold("latency", 100.0)
        self.pm.record("latency", 150.0)
        assert len(self.pm.get_alerts()) == 1

    def test_no_alert(self):
        self.pm.set_threshold("latency", 100.0)
        self.pm.record("latency", 50.0)
        assert len(self.pm.get_alerts()) == 0

    def test_clear_alerts(self):
        self.pm.record("x", 999)
        self.pm.clear_alerts()
        assert len(self.pm.get_alerts()) == 0


class TestPersistenceHooks:
    def setup_method(self):
        self.ph = PersistenceHooks()

    def test_register_fire(self):
        received = []
        self.ph.register("before_save", lambda d: received.append(d))
        self.ph.fire("before_save", {"table": "users"})
        assert len(received) == 1

    def test_unregister(self):
        handler = lambda d: None
        self.ph.register("test", handler)
        assert self.ph.unregister("test", handler) is True

    def test_history(self):
        self.ph.fire("event1")
        h = self.ph.get_history()
        assert len(h) == 1


class TestPersistenceValidator:
    def setup_method(self):
        self.pv = PersistenceValidator()

    def test_valid_config(self):
        cfg = PersistenceConfiguration()
        result = self.pv.validate_config(cfg)
        assert result.valid is True

    def test_invalid_config(self):
        cfg = PersistenceConfiguration()
        cfg.pool_size = -1
        result = self.pv.validate_config(cfg)
        assert result.valid is False


# ═══════════════════════════════════════════════════════════════════════
# MODULE 2 EXPANSION: SQL extras
# ═══════════════════════════════════════════════════════════════════════

from layers.layer13_persistence.modules.sql_database_platform.database_engine import DatabaseEngine
from layers.layer13_persistence.modules.sql_database_platform.database_factory import DatabaseFactory
from layers.layer13_persistence.modules.sql_database_platform.query_builder import QueryBuilder
from layers.layer13_persistence.modules.sql_database_platform.unit_of_work import UnitOfWork
from layers.layer13_persistence.modules.sql_database_platform.sql_compiler import SQLCompiler
from layers.layer13_persistence.modules.sql_database_platform.savepoint_manager import SavePointManager
from layers.layer13_persistence.modules.sql_database_platform.isolation_level import IsolationLevel, IsolationManager
from layers.layer13_persistence.modules.sql_database_platform.constraint_manager import ConstraintManager, DatabaseConstraint
from layers.layer13_persistence.modules.sql_database_platform.view_manager import ViewManager, DatabaseView
from layers.layer13_persistence.modules.sql_database_platform.read_replica_manager import ReadReplicaManager
from layers.layer13_persistence.modules.sql_database_platform.retry_policy import RetryPolicy
from layers.layer13_persistence.modules.sql_database_platform.sequence_manager import SequenceManager
from layers.layer13_persistence.modules.sql_database_platform.stored_procedure_manager import StoredProcedureManager, StoredProcedure
from layers.layer13_persistence.modules.sql_database_platform.materialized_view_manager import MaterializedViewManager, MaterializedView
from layers.layer13_persistence.modules.sql_database_platform.statistics_collector import StatisticsCollector
from layers.layer13_persistence.modules.sql_database_platform.connection_monitor import ConnectionMonitor


class TestDatabaseEngine:
    def test_create(self):
        e = DatabaseEngine("postgresql")
        assert e.get_type() == "postgresql"
    def test_connect(self):
        e = DatabaseEngine()
        assert e.connect() is True
        assert e.is_connected() is True
    def test_disconnect(self):
        e = DatabaseEngine()
        e.connect()
        e.disconnect()
        assert e.is_connected() is False

class TestDatabaseFactory:
    def test_create(self):
        e = DatabaseFactory.create("postgresql")
        assert e is not None
    def test_supported(self):
        assert "postgresql" in DatabaseFactory.supported()

class TestQueryBuilder:
    def test_simple(self):
        sql = QueryBuilder().table("users").select("id", "name").build()
        assert "SELECT id, name FROM users" in sql
    def test_where(self):
        sql = QueryBuilder().table("users").where("active = 1").build()
        assert "WHERE active = 1" in sql
    def test_order_limit(self):
        sql = QueryBuilder().table("t").order_by("id").limit(10).build()
        assert "ORDER BY id ASC" in sql
        assert "LIMIT 10" in sql

class TestUnitOfWork:
    def test_register(self):
        uow = UnitOfWork()
        uow.register_new("entity1")
        uow.register_dirty("entity2")
        pending = uow.get_pending()
        assert pending["new"] == 1
    def test_commit(self):
        uow = UnitOfWork()
        assert uow.commit() is True
        assert uow.is_committed() is True
    def test_rollback(self):
        uow = UnitOfWork()
        uow.register_new("e")
        uow.rollback()
        assert uow.get_pending()["new"] == 0

class TestSQLCompiler:
    def test_select(self):
        sql = SQLCompiler().compile_select("users", ["id", "name"])
        assert "SELECT id, name FROM users" in sql
    def test_insert(self):
        sql = SQLCompiler().compile_insert("users", {"name": "alice"})
        assert "INSERT INTO users" in sql
    def test_update(self):
        sql = SQLCompiler().compile_update("users", {"name": "bob"}, {"id": 1})
        assert "UPDATE users SET" in sql
    def test_delete(self):
        sql = SQLCompiler().compile_delete("users", {"id": 1})
        assert "DELETE FROM users WHERE" in sql

class TestSavePointManager:
    def test_create_release(self):
        spm = SavePointManager()
        sp = spm.create("sp1")
        assert spm.release("sp1") is True
    def test_rollback_to(self):
        spm = SavePointManager()
        spm.create("sp1")
        assert spm.rollback_to("sp1") is True

class TestIsolationManager:
    def test_set_get(self):
        im = IsolationManager()
        im.set_level(IsolationLevel.SERIALIZABLE)
        assert im.get_level() == IsolationLevel.SERIALIZABLE
    def test_name(self):
        im = IsolationManager()
        assert im.get_level_name() == "READ COMMITTED"

class TestConstraintManager:
    def test_add(self):
        cm = ConstraintManager()
        c = DatabaseConstraint("pk_users", "users", "primary_key", ["id"])
        cm.add(c)
        assert cm.get("pk_users") is not None
    def test_by_table(self):
        cm = ConstraintManager()
        cm.add(DatabaseConstraint("c1", "users", "unique", ["email"]))
        assert len(cm.get_for_table("users")) == 1

class TestViewManager:
    def test_create(self):
        vm = ViewManager()
        v = DatabaseView("v_users", "SELECT * FROM users")
        vm.create(v)
        assert vm.get("v_users") is not None
    def test_materialized(self):
        vm = ViewManager()
        vm.create(DatabaseView("mv1", "SELECT 1", materialized=True))
        assert len(vm.list_materialized()) == 1

class TestReadReplicaManager:
    def test_add_next(self):
        rm = ReadReplicaManager()
        rm.add("replica1.local")
        rm.add("replica2.local")
        r = rm.get_next()
        assert r is not None
    def test_empty(self):
        rm = ReadReplicaManager()
        assert rm.get_next() is None

class TestRetryPolicy:
    def test_execute(self):
        rp = RetryPolicy(max_retries=2)
        result = rp.execute(lambda: "ok")
        assert result == "ok"
    def test_delay(self):
        rp = RetryPolicy()
        d = rp.get_delay(0)
        assert d > 0

class TestSequenceManager:
    def test_next(self):
        sm = SequenceManager()
        sm.create("seq1")
        v1 = sm.next_value("seq1")
        v2 = sm.next_value("seq1")
        assert v2 > v1

class TestStoredProcedureManager:
    def test_register_call(self):
        spm = StoredProcedureManager()
        sp = StoredProcedure("get_user", lambda p: {"id": 1})
        spm.register(sp)
        result = spm.call("get_user")
        assert result["id"] == 1

class TestMaterializedViewManager:
    def test_create_refresh(self):
        mvm = MaterializedViewManager()
        mv = MaterializedView("mv1", "SELECT 1")
        mvm.create(mv)
        assert mvm.refresh("mv1") is True

class TestStatisticsCollector:
    def test_record(self):
        sc = StatisticsCollector()
        sc.record_table_stat("users", 1000, 50000)
        assert sc.get_table_stat("users")["rows"] == 1000

class TestConnectionMonitor:
    def test_record(self):
        cm = ConnectionMonitor()
        cm.record_connect("db1", 5.0)
        assert cm.get_connection("db1")["status"] == "connected"


# ═══════════════════════════════════════════════════════════════════════
# MODULE 3 EXPANSION: Redis extras
# ═══════════════════════════════════════════════════════════════════════

from layers.layer13_persistence.modules.redis_platform.bloom_filter import BloomFilter
from layers.layer13_persistence.modules.redis_platform.hyperloglog import HyperLogLog
from layers.layer13_persistence.modules.redis_platform.redis_sentinel import RedisSentinel
from layers.layer13_persistence.modules.redis_platform.redis_config import RedisConfig


class TestBloomFilter:
    def test_add_might(self):
        bf = BloomFilter(size=1000)
        bf.add("hello")
        assert bf.might_contain("hello") is True
        assert bf.might_contain("world") is False
    def test_fill_rate(self):
        bf = BloomFilter(size=100)
        for i in range(50):
            bf.add(str(i))
        assert bf.fill_rate() > 0

class TestHyperLogLog:
    def test_add_count(self):
        hll = HyperLogLog()
        for i in range(1000):
            hll.add(f"item_{i}")
        count = hll.count()
        assert count > 0

class TestRedisSentinel:
    def test_master_failover(self):
        s = RedisSentinel()
        s.set_master("m1", 6379)
        r1 = s.add_sentinel("r1", 6380)
        r1.role = "replica"
        s.failover()
        assert s.get_master().host == "r1"

class TestRedisConfig:
    def test_defaults(self):
        cfg = RedisConfig()
        assert cfg.port == 6379
    def test_from_dict(self):
        cfg = RedisConfig.from_dict({"host": "remote.host", "port": 6380})
        assert cfg.host == "remote.host"


# ═══════════════════════════════════════════════════════════════════════
# MODULE 4 EXPANSION: Vector extras
# ═══════════════════════════════════════════════════════════════════════

from layers.layer13_persistence.modules.vector_database_platform.vector_manager import VectorManager
from layers.layer13_persistence.modules.vector_database_platform.namespace_manager import NamespaceManager
from layers.layer13_persistence.modules.vector_database_platform.embedding_version import EmbeddingVersionManager
from layers.layer13_persistence.modules.vector_database_platform.embedding_health import EmbeddingHealth
from layers.layer13_persistence.modules.vector_database_platform.vector_events import VectorEvents


class TestVectorManager:
    def test_create_search(self):
        vm = VectorManager()
        store = vm.create_store("docs", 3)
        vm.upsert("docs", [1.0, 0.0, 0.0], {"label": "a"})
        results = vm.search("docs", [1.0, 0.0, 0.0], top_k=1)
        assert len(results) == 1

class TestNamespaceManager:
    def test_create(self):
        nm = NamespaceManager()
        ns = nm.create("users", 768)
        assert ns.dimensions == 768
    def test_count(self):
        nm = NamespaceManager()
        nm.create("a")
        assert nm.count() == 1

class TestEmbeddingVersionManager:
    def test_add_latest(self):
        evm = EmbeddingVersionManager()
        evm.add_version("gpt", 1536)
        evm.add_version("gpt", 3072)
        latest = evm.get_latest("gpt")
        assert latest.dimensions == 3072

class TestEmbeddingHealth:
    def test_check(self):
        eh = EmbeddingHealth()
        eh.check("qdrant", True, 2.0)
        assert eh.is_healthy() is True

class TestVectorEvents:
    def test_publish_subscribe(self):
        ve = VectorEvents()
        received = []
        ve.subscribe("inserted", lambda e: received.append(e))
        ve.publish("inserted", {"id": 1})
        assert len(received) == 1


# ═══════════════════════════════════════════════════════════════════════
# MODULE 5 EXPANSION: Object Storage extras
# ═══════════════════════════════════════════════════════════════════════

from layers.layer13_persistence.modules.object_storage_platform.bucket_manager import BucketManager
from layers.layer13_persistence.modules.object_storage_platform.lifecycle_policy import LifecyclePolicyManager, LifecyclePolicy
from layers.layer13_persistence.modules.object_storage_platform.file_validator import FileValidator
from layers.layer13_persistence.modules.object_storage_platform.storage_events import StorageEvents
from layers.layer13_persistence.modules.object_storage_platform.storage_cleaner import StorageCleaner


class TestBucketManager:
    def test_create(self):
        bm = BucketManager()
        b = bm.create("mybucket", "eu-west-1")
        assert b.region == "eu-west-1"
    def test_delete(self):
        bm = BucketManager()
        bm.create("b")
        assert bm.delete("b") is True

class TestLifecyclePolicyManager:
    def test_evaluate(self):
        lpm = LifecyclePolicyManager()
        p = LifecyclePolicy("archive", "logs/")
        p.expiration_days = 90
        lpm.add(p)
        assert lpm.evaluate("logs/2024.log", 91) == "expired"

class TestFileValidator:
    def test_valid(self):
        fv = FileValidator(max_size_bytes=1024)
        assert fv.is_valid("file.txt", 500) is True
    def test_too_large(self):
        fv = FileValidator(max_size_bytes=100)
        assert fv.is_valid("file.txt", 200) is False

class TestStorageEvents:
    def test_publish(self):
        se = StorageEvents()
        received = []
        se.subscribe("uploaded", lambda e: received.append(e))
        se.publish("uploaded", {"key": "photo.jpg"})
        assert len(received) == 1

class TestStorageCleaner:
    def test_clean(self):
        sc = StorageCleaner()
        sc.add_rule("old", max_age_days=30)
        objects = [{"created_at": 0}]  # very old
        removed = sc.clean(objects)
        assert removed == 1


# ═══════════════════════════════════════════════════════════════════════
# MODULE 6 EXPANSION: Memory Router
# ═══════════════════════════════════════════════════════════════════════

from layers.layer13_persistence.modules.ai_memory_persistence.memory_router import MemoryRouter


class TestMemoryRouter:
    def test_route(self):
        mr = MemoryRouter()
        cs = ConversationMemoryStore()
        mr.register_store("conv", cs)
        mr.route("conversation", "conv")
        mr.store("conversation", "k1", {"role": "user"})
        assert mr.retrieve("conversation", "k1") is not None

    def test_no_route(self):
        mr = MemoryRouter()
        assert mr.retrieve("unknown", "k") is None


# ═══════════════════════════════════════════════════════════════════════
# MODULE 7 EXPANSION: Entity Manager
# ═══════════════════════════════════════════════════════════════════════

from layers.layer13_persistence.modules.repository_layer.entity_manager import EntityManager


class TestEntityManager:
    def test_register(self):
        em = EntityManager()
        repo = BaseRepository("test")
        em.register("test", repo)
        assert em.get_repository("test") is not None

    def test_stats(self):
        em = EntityManager()
        s = em.stats()
        assert s["repositories"] == 0


# ═══════════════════════════════════════════════════════════════════════
# MODULE 8 EXPANSION: Event Bus + Backup History
# ═══════════════════════════════════════════════════════════════════════

from layers.layer13_persistence.modules.event_store.event_bus import PersistenceEventBus
from layers.layer13_persistence.modules.backup_dr.backup_history import BackupHistory


class TestPersistenceEventBus:
    def test_publish_subscribe(self):
        bus = PersistenceEventBus()
        received = []
        bus.subscribe("saved", lambda d: received.append(d))
        bus.publish("saved", {"key": "k1"})
        assert len(received) == 1
    def test_get_events(self):
        bus = PersistenceEventBus()
        bus.publish("a", {})
        bus.publish("b", {})
        assert len(bus.get_events()) == 2

class TestBackupHistory:
    def test_record(self):
        bh = BackupHistory()
        entry = bh.record("full", 1024, 50.0)
        assert entry.size_bytes == 1024
    def test_total_size(self):
        bh = BackupHistory()
        bh.record("full", 500)
        bh.record("incr", 200)
        assert bh.total_size() == 700


# ═══════════════════════════════════════════════════════════════════════
# MODULE 10 EXPANSION: Security + API
# ═══════════════════════════════════════════════════════════════════════

from layers.layer13_persistence.modules.universal_orchestrator.persistence_security import PersistenceSecurity
from layers.layer13_persistence.modules.universal_orchestrator.persistence_api import PersistenceAPI


class TestPersistenceSecurity:
    def test_allowed(self):
        ps = PersistenceSecurity()
        ps.allow_origin("app.local")
        assert ps.is_allowed("app.local") is True
    def test_blocked(self):
        ps = PersistenceSecurity()
        ps.block_pattern("malicious")
        assert ps.is_allowed("malicious_site") is False
    def test_audit(self):
        ps = PersistenceSecurity()
        ps.audit("write", "user1")
        assert len(ps.get_audit_log()) == 1
    def test_hash(self):
        ps = PersistenceSecurity()
        h = ps.hash_data(b"test")
        assert len(h) == 64

class TestPersistenceAPI:
    def test_store_retrieve(self):
        api = PersistenceAPI()
        from layers.layer13_persistence.modules.redis_platform.redis_client import RedisClient
        rc = RedisClient()
        rc.connect()
        api.register_backend("redis", rc)
        assert api.store("redis", "k1", "v1") is True
        assert api.retrieve("redis", "k1") == "v1"
    def test_delete(self):
        api = PersistenceAPI()
        rc = RedisClient()
        rc.connect()
        api.register_backend("redis", rc)
        api.store("redis", "k1", "v1")
        assert api.delete("redis", "k1") is True
