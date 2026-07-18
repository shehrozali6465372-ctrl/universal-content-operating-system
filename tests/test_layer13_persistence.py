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
