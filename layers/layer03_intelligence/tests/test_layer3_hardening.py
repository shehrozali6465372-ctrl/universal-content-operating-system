import time

import pytest

from layers.layer03_intelligence.modules.intelligence_memory.intel_cache import IntelligenceCache
from layers.layer03_intelligence.modules.intelligence_memory.intelligence_store import IntelligenceStore
from layers.layer03_intelligence.modules.trend_intelligence.trend_history import TrendHistory
from layers.layer03_intelligence.modules.reasoning_engine.multi_objective_optimizer import MultiObjectiveOptimizer, Objective
from layers.layer03_intelligence.modules.reasoning_engine.decision_graph import DecisionGraph
from layers.layer03_intelligence.modules.strategy_engine.strategy_memory import StrategyMemory
from layers.layer03_intelligence.modules.content_understanding.batch_processor import BatchProcessor
from layers.layer03_intelligence.modules.learning_signals.signal_collector import SignalCollector


def test_cache_is_bounded_and_defensive():
    cache = IntelligenceCache(max_size=1, ttl_seconds=60)
    data = {"nested": {"x": 1}}
    cache.store("a", data)
    data["nested"]["x"] = 9
    assert cache.get("a")["nested"]["x"] == 1
    got = cache.get("a")
    got["nested"]["x"] = 7
    assert cache.get("a")["nested"]["x"] == 1
    cache.store("b", {"x": 2})
    assert cache.get("a") is None
    assert cache.get("b") == {"x": 2}


def test_cache_ttl_expires(monkeypatch):
    clock = {"now": 100.0}
    monkeypatch.setattr(time, "monotonic", lambda: clock["now"])
    cache = IntelligenceCache(max_size=2, ttl_seconds=10)
    cache.store("a", {"x": 1})
    clock["now"] = 111.0
    assert cache.get("a") is None


def test_store_indexes_stay_consistent():
    store = IntelligenceStore(max_size=2)
    entry = store.store("topic", {"x": 1}, tags=["a", "b"])
    store.update(entry.entry_id, tags=["c"])
    assert store.get_by_tag("a") == []
    assert [x.entry_id for x in store.get_by_tag("c")] == [entry.entry_id]
    store.delete(entry.entry_id)
    assert store.get_by_category("topic") == []
    assert store.get_by_tag("c") == []


def test_store_rejects_invalid_confidence():
    with pytest.raises(ValueError):
        IntelligenceStore().store("x", {}, confidence=1.1)


def test_trend_history_declining_does_not_reference_missing_attribute():
    history = TrendHistory()
    history.record("topic", score=0.9, lifecycle_stage="declining")
    history.record("topic", score=0.8, lifecycle_stage="declining")
    history.record("topic", score=0.7, lifecycle_stage="declining")
    assert history.get_declining_topics() == ["topic"]


def test_minimize_objective_affects_best_compromise():
    optimizer = MultiObjectiveOptimizer()
    optimizer.add_objective(Objective("cost", weight=1.0, direction="minimize"))
    result = optimizer.optimize({
        "cheap": {"cost": 0.1},
        "expensive": {"cost": 0.9},
    })
    assert result.best_compromise is not None
    assert result.best_compromise.name == "cheap"



def test_store_returns_isolated_snapshot():
    store = IntelligenceStore()
    source = {"nested": {"x": 1}}
    entry = store.store("topic", source)
    source["nested"]["x"] = 9
    entry.data["nested"]["x"] = 7
    assert store.get(entry.entry_id).data["nested"]["x"] == 1


def test_decision_graph_rejects_cycles():
    graph = DecisionGraph()
    graph.create_node("a", "A")
    graph.create_node("b", "B", dependencies=["a"])
    with pytest.raises(ValueError):
        graph.add_edge("b", "a", "depends_on")


def test_strategy_memory_rebuilds_index_after_eviction():
    memory = StrategyMemory(max_size=2)
    first = memory.store({"strategy_id": "one"})
    memory.store({"strategy_id": "two"})
    memory.store({"strategy_id": "three"})
    assert memory.get(first.record_id) is None
    assert [r.strategy_id for r in memory.get_by_strategy("two")] == ["two"]
    assert [r.strategy_id for r in memory.get_by_strategy("three")] == ["three"]


class _Analyzer:
    def analyze(self, text):
        return {"text": text}


def test_batch_processor_cache_is_bounded():
    processor = BatchProcessor(_Analyzer(), max_cache_size=2)
    processor.analyze_with_cache("a")
    processor.analyze_with_cache("b")
    processor.analyze_with_cache("c")
    assert processor.cache_size() == 2


def test_signal_collector_is_bounded():
    collector = SignalCollector(max_signals=2)
    collector.add("a", "x", 1)
    collector.add("b", "x", 2)
    collector.add("c", "x", 3)
    assert collector.count() == 2
