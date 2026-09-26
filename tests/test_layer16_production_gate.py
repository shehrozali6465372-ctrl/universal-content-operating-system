"""Layer 16 adversarial production-contract tests."""
from datetime import datetime, timezone
import pytest
from layers.layer16_database_engineering.modules.audit_trail.audit_trail import AuditAction, AuditTrail
from layers.layer16_database_engineering.modules.backup_manager.backup_manager import BackupManager
from layers.layer16_database_engineering.modules.cache_layer.cache_layer import CacheLayer
from layers.layer16_database_engineering.modules.connection_pool.connection_pool import ConnectionPool
from layers.layer16_database_engineering.modules.index_manager.index_manager import IndexManager
from layers.layer16_database_engineering.modules.migration_engine.migration_engine import MigrationEngine
from layers.layer16_database_engineering.modules.object_mapper.object_mapper import ObjectMapper
from layers.layer16_database_engineering.modules.query_builder.query_builder import QueryBuilder
from layers.layer16_database_engineering.modules.recovery_manager.recovery_manager import RecoveryManager
from layers.layer16_database_engineering.modules.repository_pattern.repository_pattern import BaseRepository
from layers.layer16_database_engineering.modules.repository_registry.repository_registry import RepositoryRegistry
from layers.layer16_database_engineering.modules.schema_validator.schema_validator import ColumnDef, ColumnType, SchemaValidator, TableSchema
from layers.layer16_database_engineering.modules.transaction_manager.transaction_manager import DBTransactionManager, TxState

def test_query_builder_is_parameterized_and_rejects_injection():
    with pytest.raises(ValueError): QueryBuilder("users;DROP").select("*")
    with pytest.raises(ValueError): QueryBuilder("users").where("name;DROP","=","x")
    q=QueryBuilder("users").select("id","name").where_in("id",[1,2]).order_by("id")
    assert q.build()=="SELECT id, name FROM users WHERE id IN (?, ?) ORDER BY id ASC"
    assert q.build_params()==[1,2]
    assert "1 = 0" in QueryBuilder("users").where_in("id",[]).build()

def test_connection_pool_honors_bounds_timeout_and_release():
    p=ConnectionPool(min_size=1,max_size=1);p.initialize();c=p.acquire(timeout=0)
    assert c is not None and p.acquire(timeout=0) is None
    assert p.release(c) and p.acquire(timeout=0) is c
    with pytest.raises(ValueError): ConnectionPool(min_size=2,max_size=1)

def test_transaction_compensates_only_completed_operations():
    m=DBTransactionManager();events=[];tx=m.begin()
    m.add_operation(tx.tx_id,"one",lambda:events.append("one"),lambda:events.append("undo-one"))
    m.add_operation(tx.tx_id,"two",lambda:(_ for _ in ()).throw(RuntimeError("boom")),lambda:events.append("undo-two"))
    result=m.commit(tx.tx_id)
    assert result["rolled_back"] and events==["one","undo-one"]
    assert m.get_transaction(tx.tx_id).state==TxState.FAILED

def test_repository_index_rebuilds_after_update_delete():
    r=BaseRepository("item");r.create_index("kind");row=r.add({"kind":"a"},entity_id="1")
    assert r.find_by_index("kind","a")==[row]
    r.update("1",{"kind":"b"});assert r.find_by_index("kind","a")==[]
    assert r.find_by_index("kind","b")[0]["id"]=="1"
    r.delete("1");assert r.find_by_index("kind","b")==[]

def test_recovery_executes_steps_and_reports_failure():
    m=RecoveryManager();events=[]
    plan=m.create_plan("restore",[{"name":"restore","execute":lambda:events.append("restore")},
                                   {"name":"verify","execute":lambda:(_ for _ in ()).throw(RuntimeError("bad"))}])
    result=m.execute_plan(plan.plan_id)
    assert result["status"]=="failed" and events==["restore"] and m.get_state()=="failed"

def test_migration_duplicate_and_failure_are_visible():
    e=MigrationEngine();e.add_migration("001","ok",lambda:None)
    with pytest.raises(ValueError): e.add_migration("001","dup",lambda:None)
    e.add_migration("002","bad",lambda:(_ for _ in ()).throw(RuntimeError("failed")))
    assert e.migrate_up()["failed"]["version"]=="002"

def test_schema_validation_checks_types_unknown_and_required():
    v=SchemaValidator();v.register_schema(TableSchema("users",[
        ColumnDef("id",ColumnType.INTEGER,nullable=False,primary_key=True),
        ColumnDef("name",ColumnType.TEXT,nullable=False,max_length=10),
        ColumnDef("created",ColumnType.DATETIME)]))
    assert v.validate("users",{"id":1,"name":"Ali","created":datetime.now(timezone.utc)})["valid"]
    bad=v.validate("users",{"id":"1","name":"too-long-name","extra":1})
    assert not bad["valid"] and any("Unknown column" in x for x in bad["errors"])

def test_cache_uses_real_access_recency():
    c=CacheLayer(2);c.set("a",1);c.set("b",2);assert c.get("a")==1;c.set("c",3)
    assert c.get("a")==1 and c.get("b") is None

def test_backup_snapshot_is_immutable_and_verifiable():
    b=BackupManager();source={"nested":{"value":1}};entry=b.create_backup("x",source);source["nested"]["value"]=9
    assert b.restore(entry.backup_id)["nested"]["value"]==1 and b.verify(entry.backup_id)

def test_audit_is_bounded_and_copies_payloads():
    a=AuditTrail(2);payload={"v":1};a.log(AuditAction.CREATE,"users","1",new_data=payload);payload["v"]=2
    a.log(AuditAction.UPDATE,"users","1",new_data=payload);a.log(AuditAction.DELETE,"users","1")
    rows=a.query(limit=10);assert len(rows)==2 and rows[-1]["action"]=="delete"

def test_registry_and_index_reject_duplicate_or_unsafe_state():
    i=IndexManager();i.create_index("idx_users_name","users",["name"])
    with pytest.raises(ValueError): i.create_index("idx_users_name","users",["name"])
    with pytest.raises(ValueError): i.create_index("bad;drop","users",["name"])
    r=RepositoryRegistry();r.register("users",object())
    with pytest.raises(ValueError): r.register("users",object())

def test_object_mapper_requires_registered_mapping():
    m=ObjectMapper()
    with pytest.raises(KeyError):m.map_object("A","B",{"x":1})
    mapping=m.register("A","B");mapping.map_field("x","y",lambda x:x+1)
    assert m.map_object("A","B",{"x":1})=={"y":2}
