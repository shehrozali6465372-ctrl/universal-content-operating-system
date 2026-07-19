"""Tests for Phase 3 — Database Engineering (15 modules)."""
from __future__ import annotations
import time
import pytest

# ─── Repository Pattern ────────────────────────────────────────────
from layers.layer16_database_engineering.modules.repository_pattern.repository_pattern import BaseRepository

class TestRepositoryPattern:
    def setup_method(self):
        self.repo = BaseRepository("users")

    def test_add_get(self):
        rec = self.repo.add({"name": "Ali", "age": 30})
        assert rec["name"] == "Ali"
        assert self.repo.get(rec["id"])["name"] == "Ali"

    def test_update(self):
        rec = self.repo.add({"name": "Ali"})
        self.repo.update(rec["id"], {"name": "Ahmed"})
        assert self.repo.get(rec["id"])["name"] == "Ahmed"

    def test_delete(self):
        rec = self.repo.add({"name": "Ali"})
        assert self.repo.delete(rec["id"])
        assert self.repo.get(rec["id"]) is None

    def test_find_by(self):
        self.repo.add({"name": "Ali", "role": "admin"})
        self.repo.add({"name": "Bob", "role": "user"})
        results = self.repo.find_by("role", "admin")
        assert len(results) == 1

    def test_index(self):
        self.repo.add({"name": "Ali", "role": "admin"})
        self.repo.add({"name": "Bob", "role": "user"})
        self.repo.create_index("role")
        results = self.repo.find_by_index("role", "admin")
        assert len(results) == 1

    def test_bulk_add(self):
        items = [{"name": f"user_{i}"} for i in range(5)]
        self.repo.bulk_add(items)
        assert self.repo.count() == 5

    def test_clear(self):
        self.repo.add({"name": "a"})
        assert self.repo.clear() == 1
        assert self.repo.count() == 0


# ─── ORM Layer ─────────────────────────────────────────────────────
from layers.layer16_database_engineering.modules.orm_layer.orm_layer import BaseModel, ModelMeta, Field

class TestORMLayer:
    def setup_method(self):
        class User(BaseModel):
            _meta = ModelMeta("users", [
                Field("id", "text", primary_key=True),
                Field("name", "text", nullable=False),
                Field("email", "text"),
            ])
        self.User = User
        self.User.clear()

    def test_create_save(self):
        user = self.User(id="u1", name="Ali", email="a@test.com")
        data = user.save()
        assert data["name"] == "Ali"

    def test_get_by_id(self):
        user = self.User(id="u1", name="Ali")
        user.save()
        record = self.User.get_by_id("u1")
        assert record["name"] == "Ali"

    def test_filter_by(self):
        self.User(id="u1", name="Ali", email="a@test.com").save()
        self.User(id="u2", name="Bob", email="b@test.com").save()
        results = self.User.filter_by(name="Ali")
        assert len(results) == 1

    def test_delete(self):
        self.User(id="u1", name="Ali").save()
        assert self.User.delete("u1")
        assert self.User.count() == 0


# ─── Connection Pool ───────────────────────────────────────────────
from layers.layer16_database_engineering.modules.connection_pool.connection_pool import ConnectionPool, ConnectionState

class TestConnectionPool:
    def setup_method(self):
        self.pool = ConnectionPool(min_size=2, max_size=5)

    def test_initialize(self):
        count = self.pool.initialize()
        assert count == 2
        assert self.pool.stats()["total"] == 2

    def test_acquire_release(self):
        self.pool.initialize()
        conn = self.pool.acquire()
        assert conn is not None
        assert conn.state == ConnectionState.ACTIVE
        self.pool.release(conn)
        assert conn.state == ConnectionState.IDLE

    def test_stats(self):
        self.pool.initialize()
        stats = self.pool.stats()
        assert stats["total"] == 2
        assert stats["idle"] == 2


# ─── Query Builder ─────────────────────────────────────────────────
from layers.layer16_database_engineering.modules.query_builder.query_builder import QueryBuilder

class TestQueryBuilder:
    def test_simple_select(self):
        q = QueryBuilder("users").select("name", "email")
        assert "SELECT name, email FROM users" in q.build()

    def test_where(self):
        q = QueryBuilder("users").where_eq("active", True).limit(10)
        sql = q.build()
        assert "WHERE" in sql
        assert "LIMIT 10" in sql

    def test_order_by(self):
        q = QueryBuilder("users").order_by("name", "DESC")
        assert "ORDER BY name DESC" in q.build()

    def test_join(self):
        q = QueryBuilder("users").join("orders", "users.id = orders.user_id")
        assert "JOIN orders" in q.build()

    def test_fluent_chaining(self):
        sql = (QueryBuilder("users")
               .select("name")
               .where_eq("active", True)
               .order_by("name")
               .limit(5)
               .build())
        assert "SELECT name" in sql
        assert "WHERE active = ?" in sql
        assert "ORDER BY name" in sql
        assert "LIMIT 5" in sql


# ─── Migration Engine ──────────────────────────────────────────────
from layers.layer16_database_engineering.modules.migration_engine.migration_engine import MigrationEngine, MigrationStatus

class TestMigrationEngine:
    def setup_method(self):
        self.me = MigrationEngine()

    def test_add_migrate_up(self):
        applied = []
        self.me.add_migration("001", "create_users", lambda: applied.append("users"))
        self.me.add_migration("002", "create_posts", lambda: applied.append("posts"))
        result = self.me.migrate_up()
        assert len(result["applied"]) == 2
        assert applied == ["users", "posts"]

    def test_migrate_down(self):
        self.me.add_migration("001", "create_users", lambda: None, lambda: None)
        self.me.migrate_up()
        result = self.me.migrate_down("001")
        assert len(result["rolled_back"]) == 1

    def test_current_version(self):
        self.me.add_migration("001", "v1", lambda: None)
        self.me.migrate_up()
        assert self.me.current_version() == "001"

    def test_pending(self):
        self.me.add_migration("001", "v1", lambda: None)
        self.me.add_migration("002", "v2", lambda: None)
        self.me.migrate_up("001")
        pending = self.me.pending()
        assert len(pending) == 1


# ─── Schema Validator ──────────────────────────────────────────────
from layers.layer16_database_engineering.modules.schema_validator.schema_validator import SchemaValidator, TableSchema, ColumnDef, ColumnType

class TestSchemaValidator:
    def setup_method(self):
        self.sv = SchemaValidator()
        schema = TableSchema("users", [
            ColumnDef("id", ColumnType.TEXT, primary_key=True),
            ColumnDef("name", ColumnType.TEXT, nullable=False),
            ColumnDef("email", ColumnType.TEXT, max_length=100),
        ])
        self.sv.register_schema(schema)

    def test_valid(self):
        result = self.sv.validate("users", {"id": "1", "name": "Ali"})
        assert result["valid"]

    def test_missing_required(self):
        result = self.sv.validate("users", {"id": "1"})
        assert not result["valid"]

    def test_max_length(self):
        result = self.sv.validate("users", {"id": "1", "name": "A", "email": "x" * 101})
        assert not result["valid"]


# ─── Cache Layer ───────────────────────────────────────────────────
from layers.layer16_database_engineering.modules.cache_layer.cache_layer import CacheLayer

class TestCacheLayer:
    def setup_method(self):
        self.cache = CacheLayer(max_size=100)

    def test_set_get(self):
        self.cache.set("key1", "value1")
        assert self.cache.get("key1") == "value1"

    def test_ttl_expiry(self):
        self.cache.set("key1", "value1", ttl=0.01)
        time.sleep(0.02)
        assert self.cache.get("key1") is None

    def test_lru_eviction(self):
        cache = CacheLayer(max_size=3)
        for i in range(5):
            cache.set(f"key_{i}", i)
        assert cache.size() == 3

    def test_stats(self):
        self.cache.set("a", 1)
        self.cache.get("a")
        self.cache.get("missing")
        stats = self.cache.stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1


# ─── DB Transaction Manager ────────────────────────────────────────
from layers.layer16_database_engineering.modules.transaction_manager.transaction_manager import DBTransactionManager, TxState

class TestDBTransactionManager:
    def setup_method(self):
        self.tm = DBTransactionManager()

    def test_begin_commit(self):
        tx = self.tm.begin()
        self.tm.add_operation(tx.tx_id, "insert", lambda: "ok")
        result = self.tm.commit(tx.tx_id)
        assert result["status"] == "committed"

    def test_rollback(self):
        tx = self.tm.begin()
        self.tm.add_operation(tx.tx_id, "op", lambda: "ok")
        result = self.tm.rollback(tx.tx_id)
        assert result["status"] == "rolled_back"


# ─── Audit Trail ───────────────────────────────────────────────────
from layers.layer16_database_engineering.modules.audit_trail.audit_trail import AuditTrail, AuditAction

class TestAuditTrail:
    def setup_method(self):
        self.at = AuditTrail()

    def test_log(self):
        entry = self.at.log(AuditAction.CREATE, "users", "u1", new_data={"name": "Ali"})
        assert entry.action == AuditAction.CREATE

    def test_query(self):
        self.at.log(AuditAction.CREATE, "users", "u1")
        self.at.log(AuditAction.UPDATE, "users", "u1")
        self.at.log(AuditAction.CREATE, "posts", "p1")
        results = self.at.query(table_name="users")
        assert len(results) == 2


# ─── Index Manager ─────────────────────────────────────────────────
from layers.layer16_database_engineering.modules.index_manager.index_manager import IndexManager, IndexType

class TestIndexManager:
    def setup_method(self):
        self.im = IndexManager()

    def test_create_drop(self):
        idx = self.im.create_index("idx_name", "users", ["name"])
        assert idx.index_name == "idx_name"
        assert self.im.count() == 1
        assert self.im.drop_index("idx_name")
        assert self.im.count() == 0

    def test_list_by_table(self):
        self.im.create_index("idx1", "users", ["name"])
        self.im.create_index("idx2", "posts", ["title"])
        results = self.im.list_indexes(table_name="users")
        assert len(results) == 1


# ─── Backup Manager ────────────────────────────────────────────────
from layers.layer16_database_engineering.modules.backup_manager.backup_manager import BackupManager

class TestBackupManager:
    def setup_method(self):
        self.bm = BackupManager()

    def test_create_restore(self):
        data = {"users": [{"name": "Ali"}], "posts": []}
        entry = self.bm.create_backup("snap1", data)
        restored = self.bm.restore(entry.backup_id)
        assert restored["users"][0]["name"] == "Ali"

    def test_delete(self):
        entry = self.bm.create_backup("snap1", {"data": 1})
        assert self.bm.delete_backup(entry.backup_id)
        assert self.bm.count() == 0


# ─── Recovery Manager ──────────────────────────────────────────────
from layers.layer16_database_engineering.modules.recovery_manager.recovery_manager import RecoveryManager, RecoveryState

class TestRecoveryManager:
    def setup_method(self):
        self.rm = RecoveryManager()

    def test_create_execute(self):
        plan = self.rm.create_plan("restore_db", [{"step": "stop"}])
        result = self.rm.execute_plan(plan.plan_id)
        assert result["status"] == "completed"
        assert self.rm.get_state() == RecoveryState.HEALTHY.value


# ─── Data Mapper ───────────────────────────────────────────────────
from layers.layer16_database_engineering.modules.data_mapper.data_mapper import DataMapper

class TestDataMapper:
    def setup_method(self):
        self.mapper = DataMapper("user")
        self.mapper.add_rule("first_name", "firstName", str.upper, str.lower)
        self.mapper.add_rule("email_addr", "email")

    def test_to_domain(self):
        result = self.mapper.to_domain({"first_name": "ali", "email_addr": "a@test.com"})
        assert result["firstName"] == "ALI"
        assert result["email"] == "a@test.com"

    def test_to_db(self):
        result = self.mapper.to_db({"firstName": "ALI", "email": "a@test.com"})
        assert result["first_name"] == "ali"
        assert result["email_addr"] == "a@test.com"


# ─── Object Mapper ─────────────────────────────────────────────────
from layers.layer16_database_engineering.modules.object_mapper.object_mapper import ObjectMapper

class TestObjectMapper:
    def setup_method(self):
        self.om = ObjectMapper()
        mapping = self.om.register("db_user", "domain_user")
        mapping.map_field("first_name", "firstName", str.upper)
        mapping.map_field("email", "emailAddress")

    def test_map_object(self):
        result = self.om.map_object("db_user", "domain_user",
                                     {"first_name": "ali", "email": "a@test.com"})
        assert result["firstName"] == "ALI"
        assert result["emailAddress"] == "a@test.com"


# ─── Repository Registry ───────────────────────────────────────────
from layers.layer16_database_engineering.modules.repository_registry.repository_registry import RepositoryRegistry

class TestRepositoryRegistry:
    def setup_method(self):
        self.rr = RepositoryRegistry()

    def test_register_get(self):
        repo = BaseRepository("test")
        self.rr.register("users", repo)
        assert self.rr.get("users") is repo

    def test_unregister(self):
        self.rr.register("users", BaseRepository("test"))
        assert self.rr.unregister("users")
        assert not self.rr.has("users")

    def test_list(self):
        self.rr.register("a", BaseRepository("a"))
        self.rr.register("b", BaseRepository("b"))
        assert set(self.rr.list_repositories()) == {"a", "b"}
