import time
import pytest
from layers.layer03_intelligence.modules.intelligence_memory.intel_cache import IntelligenceCache
from layers.layer03_intelligence.modules.intelligence_memory.intelligence_store import IntelligenceStore

def test_cache_is_bounded_and_defensive():
    c=IntelligenceCache(max_size=1, ttl_seconds=60)
    data={"nested":{"x":1}}
    c.store("a",data)
    data["nested"]["x"]=9
    got=c.get("a")
    assert got["nested"]["x"]==1
    got["nested"]["x"]=7
    assert c.get("a")["nested"]["x"]==1
    c.store("b",{"x":2})
    assert c.get("a") is None
    assert c.get("b")=={"x":2}

def test_cache_ttl_expires():
    c=IntelligenceCache(max_size=2, ttl_seconds=0)
    c.store("a",{"x":1})
    assert c.get("a")=={"x":1}

def test_store_indexes_stay_consistent():
    s=IntelligenceStore(max_size=2)
    e=s.store("topic",{"x":1},tags=["a","b"])
    s.update(e.entry_id,tags=["c"])
    assert s.get_by_tag("a")==[]
    assert [x.entry_id for x in s.get_by_tag("c")]==[e.entry_id]
    s.delete(e.entry_id)
    assert s.get_by_category("topic")==[]
    assert s.get_by_tag("c")==[]

def test_store_rejects_invalid_confidence():
    s=IntelligenceStore()
    with pytest.raises(ValueError):
        s.store("x",{},confidence=1.1)
