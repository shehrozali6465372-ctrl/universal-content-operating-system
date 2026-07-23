"""Tests for Redis Enterprise Features.

Covers:
- RedisClient (connection, retry, fallback, metrics)
- RedisCache (namespace, tags, hit/miss stats)
- RedisSession (create, get, update, destroy, snapshot)
- RedisRateLimiter (sliding window, token bucket)
- RedisPubSub (publish, subscribe, history)
- RedisQueue (enqueue, dequeue, priority, retry, dead letter)
- RedisManager (integration, get_redis_status)
"""
from __future__ import annotations
import os
import sys
import time
import threading
import json
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ─── RedisClient Tests ───────────────────────────────────────────

class TestRedisClient:
    def setup_method(self):
        from layers.layer13_persistence.modules.redis_platform.redis_client import RedisClient
        self.client = RedisClient()
        self.client.initialize()

    def teardown_method(self):
        self.client.flushdb()
        self.client.close()

    def test_initialize(self):
        assert self.client._initialized is True

    def test_ping(self):
        assert self.client.ping() is True

    def test_set_get(self):
        self.client.set("test_key", "test_value")
        assert self.client.get("test_key") == "test_value"

    def test_delete(self):
        self.client.set("del_key", "val")
        assert self.client.delete("del_key") >= 1
        assert self.client.get("del_key") is None

    def test_exists(self):
        self.client.set("exists_key", "val")
        assert self.client.exists("exists_key") is True
        self.client.delete("exists_key")
        assert self.client.exists("exists_key") is False

    def test_ttl(self):
        self.client.set("ttl_key", "val", ttl=10.0)
        remaining = self.client.ttl("ttl_key")
        assert 0 < remaining <= 10

    def test_ttl_no_expiry(self):
        self.client.set("no_ttl", "val")
        assert self.client.ttl("no_ttl") == -1

    def test_ttl_not_found(self):
        assert self.client.ttl("nonexistent") == -2

    def test_expire(self):
        self.client.set("exp_key", "val")
        assert self.client.expire("exp_key", 60) is True

    def test_keys_pattern(self):
        self.client.set("pat:1", "a")
        self.client.set("pat:2", "b")
        self.client.set("other", "c")
        keys = self.client.keys("pat:*")
        assert len(keys) == 2

    def test_mget_mset(self):
        self.client.mset({"m1": "v1", "m2": "v2"})
        vals = self.client.mget(["m1", "m2", "m3"])
        assert vals[0] == "v1"
        assert vals[1] == "v2"
        assert vals[2] is None

    def test_incr_decr(self):
        self.client.set("counter", "10")
        assert self.client.incr("counter") == 11
        assert self.client.decr("counter") == 10

    def test_incrby(self):
        self.client.set("incrb", "5")
        assert self.client.incrby("incrb", 10) == 15

    def test_hash_operations(self):
        self.client.hset("h1", "f1", "v1")
        self.client.hset("h1", "f2", "v2")
        assert self.client.hget("h1", "f1") == "v1"
        assert self.client.hgetall("h1") == {"f1": "v1", "f2": "v2"}
        assert self.client.hdel("h1", "f1") == 1
        assert self.client.hget("h1", "f1") is None

    def test_list_operations(self):
        self.client.rpush("lst", "a", "b", "c")
        assert self.client.llen("lst") == 3
        assert self.client.lrange("lst", 0, -1) == ["a", "b", "c"]
        assert self.client.lpop("lst") == "a"
        assert self.client.rpop("lst") == "c"
        assert self.client.llen("lst") == 1

    def test_set_operations(self):
        self.client.sadd("st", "x", "y", "z")
        assert self.client.scard("st") == 3
        assert "x" in self.client.smembers("st")
        assert self.client.srem("st", "x") == 1
        assert "x" not in self.client.smembers("st")

    def test_flushdb(self):
        self.client.set("f1", "v1")
        self.client.set("f2", "v2")
        self.client.flushdb()
        assert self.client.dbsize() == 0

    def test_dbsize(self):
        self.client.flushdb()
        self.client.set("s1", "v1")
        self.client.set("s2", "v2")
        assert self.client.dbsize() == 2

    def test_pipeline(self):
        pipe = self.client.pipeline()
        pipe.set("p1", "v1")
        pipe.set("p2", "v2")
        pipe.get("p1")
        results = pipe.execute()
        assert results == [True, True, "v1"]

    def test_get_metrics(self):
        self.client.set("m", "v")
        self.client.get("m")
        metrics = self.client.get_metrics()
        assert metrics["initialized"] is True
        assert metrics["total_ops"] >= 0
        assert "latency" in metrics
        assert "config" in metrics

    def test_auto_reconnect(self):
        assert self.client._auto_reconnect() is not None


# ─── RedisCache Tests ────────────────────────────────────────────

class TestRedisCache:
    def setup_method(self):
        from layers.layer13_persistence.modules.redis_platform.redis_client import RedisClient
        from layers.layer13_persistence.modules.redis_platform.redis_cache import RedisCache
        self.client = RedisClient()
        self.client.initialize()
        self.cache = RedisCache(self.client, namespace="test_cache")

    def teardown_method(self):
        self.cache.clear()
        self.client.close()

    def test_set_get(self):
        self.cache.set("key1", {"data": "value"})
        result = self.cache.get("key1")
        assert result == {"data": "value"}

    def test_miss(self):
        assert self.cache.get("nonexistent") is None

    def test_hit_miss_stats(self):
        self.cache.set("k", "v")
        self.cache.get("k")  # hit
        self.cache.get("miss")  # miss
        stats = self.cache.get_stats()
        assert stats["hits"] >= 1
        assert stats["misses"] >= 1

    def test_get_or_set(self):
        call_count = [0]
        def factory():
            call_count[0] += 1
            return "computed"

        result = self.cache.get_or_set("gos_key", factory)
        assert result == "computed"
        assert call_count[0] == 1

        # Second call should use cache
        result2 = self.cache.get_or_set("gos_key", factory)
        assert result2 == "computed"
        assert call_count[0] == 1  # Factory not called again

    def test_delete(self):
        self.cache.set("del", "val")
        assert self.cache.delete("del") is True
        assert self.cache.get("del") is None

    def test_tags_invalidation(self):
        self.cache.set("post:1", "data1", tags=["posts"])
        self.cache.set("post:2", "data2", tags=["posts"])
        self.cache.set("user:1", "u1", tags=["users"])

        invalidated = self.cache.invalidate_tag("posts")
        assert invalidated == 2
        assert self.cache.get("post:1") is None
        assert self.cache.get("user:1") == "u1"

    def test_exists(self):
        self.cache.set("e", "v")
        assert self.cache.exists("e") is True
        assert self.cache.exists("no") is False

    def test_keys(self):
        self.cache.set("k1", "v1")
        self.cache.set("k2", "v2")
        keys = self.cache.keys("*")
        assert len(keys) == 2

    def test_get_many(self):
        self.cache.set_many({"a": 1, "b": 2})
        result = self.cache.get_many(["a", "b", "c"])
        assert result["a"] == 1
        assert result["b"] == 2
        assert "c" not in result

    def test_clear(self):
        self.cache.set("c1", "v1")
        self.cache.set("c2", "v2")
        self.cache.clear()
        assert self.cache.get("c1") is None

    def test_reset_stats(self):
        self.cache.get("x")
        self.cache.reset_stats()
        stats = self.cache.get_stats()
        assert stats["hits"] == 0
        assert stats["misses"] == 0


# ─── RedisSession Tests ──────────────────────────────────────────

class TestRedisSession:
    def setup_method(self):
        from layers.layer13_persistence.modules.redis_platform.redis_client import RedisClient
        from layers.layer13_persistence.modules.redis_platform.redis_session import RedisSession
        self.client = RedisClient()
        self.client.initialize()
        self.sessions = RedisSession(self.client, session_ttl=3600)

    def teardown_method(self):
        self.client.flushdb()
        self.client.close()

    def test_create(self):
        session = self.sessions.create("user1", "facebook", {"topic": "AI"})
        assert session["user_id"] == "user1"
        assert session["platform"] == "facebook"
        assert session["context"]["topic"] == "AI"

    def test_get(self):
        session = self.sessions.create("user1", "twitter")
        fetched = self.sessions.get(session["session_id"])
        assert fetched["user_id"] == "user1"

    def test_get_not_found(self):
        assert self.sessions.get("nonexistent") is None

    def test_update(self):
        session = self.sessions.create("user1", "facebook")
        self.sessions.update(session["session_id"], {"platform": "instagram"})
        updated = self.sessions.get(session["session_id"])
        assert updated["platform"] == "instagram"

    def test_update_context(self):
        session = self.sessions.create("user1", "facebook", {"a": 1})
        self.sessions.update_context(session["session_id"], {"b": 2})
        updated = self.sessions.get(session["session_id"])
        assert updated["context"]["a"] == 1
        assert updated["context"]["b"] == 2

    def test_destroy(self):
        session = self.sessions.create("user1", "facebook")
        assert self.sessions.destroy(session["session_id"]) is True
        assert self.sessions.get(session["session_id"]) is None

    def test_get_user_sessions(self):
        self.sessions.create("user1", "facebook")
        self.sessions.create("user1", "twitter")
        sessions = self.sessions.get_user_sessions("user1")
        assert len(sessions) == 2

    def test_snapshot_restore(self):
        session = self.sessions.create("user1", "facebook", {"x": 1})
        snap = self.sessions.snapshot(session["session_id"])
        assert snap["context"]["x"] == 1

        self.sessions.update_context(session["session_id"], {"x": 99})
        self.sessions.restore(session["session_id"], snap)
        restored = self.sessions.get(session["session_id"])
        assert restored["context"]["x"] == 1

    def test_stats(self):
        self.sessions.create("u1", "fb")
        self.sessions.create("u2", "tw")
        stats = self.sessions.get_stats()
        assert stats["total_sessions"] >= 1
        assert stats["active_sessions"] >= 1


# ─── RedisRateLimiter Tests ──────────────────────────────────────

class TestRedisRateLimiter:
    def setup_method(self):
        from layers.layer13_persistence.modules.redis_platform.redis_client import RedisClient
        from layers.layer13_persistence.modules.redis_platform.redis_rate_limiter import RedisRateLimiter
        self.client = RedisClient()
        self.client.initialize()
        self.limiter = RedisRateLimiter(self.client)

    def teardown_method(self):
        self.client.flushdb()
        self.client.close()

    def test_sliding_window_allowed(self):
        allowed, info = self.limiter.sliding_window("user1", 5, 60)
        assert allowed is True
        assert info["remaining"] == 4

    def test_sliding_window_rejected(self):
        for _ in range(5):
            self.limiter.sliding_window("user1", 5, 60)
        allowed, info = self.limiter.sliding_window("user1", 5, 60)
        assert allowed is False
        assert info["remaining"] == 0

    def test_token_bucket_allowed(self):
        allowed, info = self.limiter.token_bucket("user2", 10, 1.0)
        assert allowed is True
        assert info["tokens_remaining"] >= 8.0

    def test_token_bucket_exhaustion(self):
        for _ in range(10):
            self.limiter.token_bucket("user3", 10, 0.1)
        allowed, info = self.limiter.token_bucket("user3", 10, 0.1)
        assert allowed is False
        assert info["retry_after"] > 0

    def test_check_and_consume(self):
        allowed, info = self.limiter.check_and_consume("ep1", 3, 60)
        assert allowed is True

    def test_reset(self):
        self.limiter.sliding_window("u", 1, 60)
        self.limiter.reset("u")
        usage = self.limiter.get_usage("u")
        assert usage["current_count"] == 0

    def test_stats(self):
        self.limiter.sliding_window("s", 1, 60)
        self.limiter.sliding_window("s", 1, 60)  # rejected
        stats = self.limiter.get_stats()
        assert stats["total_requests"] == 2
        assert stats["total_rejected"] >= 1


# ─── RedisPubSub Tests ──────────────────────────────────────────

class TestRedisPubSub:
    def setup_method(self):
        from layers.layer13_persistence.modules.redis_platform.redis_client import RedisClient
        from layers.layer13_persistence.modules.redis_platform.redis_pubsub import RedisPubSub
        self.client = RedisClient()
        self.client.initialize()
        self.pubsub = RedisPubSub(self.client)

    def teardown_method(self):
        self.client.flushdb()
        self.client.close()

    def test_publish_subscribe(self):
        received = []
        self.pubsub.subscribe("ch1", lambda c, m, t, ts: received.append(m))
        self.pubsub.publish("ch1", "hello")
        assert len(received) == 1
        assert received[0] == "hello"

    def test_pattern_subscribe(self):
        received = []
        self.pubsub.subscribe_pattern("events.*", lambda c, m, t, ts: received.append(m))
        self.pubsub.publish("events.post", "new post")
        self.pubsub.publish("events.like", "new like")
        assert len(received) == 2

    def test_unsubscribe(self):
        received = []
        callback = lambda c, m, t, ts: received.append(m)
        self.pubsub.subscribe("ch", callback)
        self.pubsub.publish("ch", "msg1")
        self.pubsub.unsubscribe("ch", callback)
        self.pubsub.publish("ch", "msg2")
        assert len(received) == 1

    def test_history(self):
        self.pubsub.publish("ch", "msg1")
        self.pubsub.publish("ch", "msg2")
        self.pubsub.publish("ch", "msg3")
        history = self.pubsub.get_history("ch", limit=2)
        assert len(history) == 2

    def test_channels(self):
        self.pubsub.publish("ch_a", "a")
        self.pubsub.publish("ch_b", "b")
        channels = self.pubsub.get_channels()
        assert len(channels) >= 2

    def test_stats(self):
        self.pubsub.publish("s", "m")
        stats = self.pubsub.get_stats()
        assert stats["total_published"] >= 1


# ─── RedisQueue Tests ────────────────────────────────────────────

class TestRedisQueue:
    def setup_method(self):
        from layers.layer13_persistence.modules.redis_platform.redis_client import RedisClient
        from layers.layer13_persistence.modules.redis_platform.redis_queue import RedisQueue
        self.client = RedisClient()
        self.client.initialize()
        self.queue = RedisQueue(self.client, name="test_queue")

    def teardown_method(self):
        self.queue.clear()
        self.client.close()

    def test_enqueue_dequeue(self):
        task_id = self.queue.enqueue("test_task", {"data": "hello"})
        task = self.queue.dequeue()
        assert task is not None
        assert task["task_type"] == "test_task"
        assert task["payload"]["data"] == "hello"

    def test_priority_order(self):
        self.queue.enqueue("low", {}, priority="low")
        self.queue.enqueue("high", {}, priority="high")
        self.queue.enqueue("normal", {}, priority="normal")

        t1 = self.queue.dequeue()
        assert t1["task_type"] == "high"

    def test_complete(self):
        task_id = self.queue.enqueue("t", {})
        self.queue.dequeue()
        assert self.queue.complete(task_id, result="done") is True
        task = self.queue.get_task(task_id)
        assert task["status"] == "completed"

    def test_fail_requeue(self):
        task_id = self.queue.enqueue("t", {}, max_retries=3)
        self.queue.dequeue()
        result = self.queue.fail(task_id, "error", requeue=True)
        assert result is True  # Requeued
        task = self.queue.get_task(task_id)
        assert task["retries"] == 1

    def test_fail_dead_letter(self):
        task_id = self.queue.enqueue("t", {}, max_retries=1)
        self.queue.dequeue()
        result = self.queue.fail(task_id, "fatal error", requeue=True)
        assert result is False  # Dead letter
        task = self.queue.get_task(task_id)
        assert task["status"] == "dead_letter"

    def test_peek(self):
        self.queue.enqueue("a", {"i": 1})
        self.queue.enqueue("b", {"i": 2})
        peeked = self.queue.peek(2)
        assert len(peeked) == 2

    def test_size(self):
        self.queue.enqueue("a", {})
        self.queue.enqueue("b", {})
        sizes = self.queue.size()
        assert sizes["total"] == 2

    def test_clear(self):
        self.queue.enqueue("a", {})
        self.queue.clear()
        sizes = self.queue.size()
        assert sizes["total"] == 0

    def test_stats(self):
        task_id = self.queue.enqueue("t", {})
        self.queue.dequeue()
        self.queue.complete(task_id)
        stats = self.queue.get_stats()
        assert stats["total_completed"] == 1
        assert stats["success_rate_pct"] == 100.0


# ─── RedisManager Integration Tests ──────────────────────────────

class TestRedisManager:
    def setup_method(self):
        from layers.layer13_persistence.modules.redis_platform.redis_manager import RedisManager, RedisConnectionConfig
        self.manager = RedisManager(RedisConnectionConfig())
        self.manager.initialize()

    def teardown_method(self):
        if self.manager._client:
            self.manager._client.flushdb()
        self.manager.close()

    def test_initialize(self):
        assert self.manager._initialized is True
        assert self.manager.cache is not None
        assert self.manager.sessions is not None
        assert self.manager.rate_limiter is not None
        assert self.manager.pubsub is not None

    def test_cache_shortcuts(self):
        self.manager.cache_set("ck", {"hello": "world"})
        assert self.manager.cache_get("ck") == {"hello": "world"}
        self.manager.cache_delete("ck")
        assert self.manager.cache_get("ck") is None

    def test_session_shortcuts(self):
        session = self.manager.create_session("u1", "fb", {"topic": "AI"})
        assert session["user_id"] == "u1"
        fetched = self.manager.get_session(session["session_id"])
        assert fetched["platform"] == "fb"

    def test_rate_limit_shortcuts(self):
        allowed, info = self.manager.check_rate_limit("ep", 5, 60)
        assert allowed is True

    def test_pubsub_shortcuts(self):
        received = []
        self.manager.subscribe_event("test_ch", lambda c, m, t, ts: received.append(m))
        self.manager.publish_event("test_ch", "hello")
        assert len(received) == 1

    def test_queue_shortcuts(self):
        task_id = self.manager.enqueue_task("generate", {"topic": "AI"})
        task = self.manager.dequeue_task()
        assert task["task_type"] == "generate"

    def test_health_check(self):
        health = self.manager.health_check()
        assert health["initialized"] is True
        assert health["overall"] in ("healthy", "degraded")

    def test_get_redis_status(self):
        status = self.manager.get_redis_status()
        assert "overall" in status
        assert "connection" in status
        assert "cache" in status
        assert "sessions" in status
        assert "rate_limiter" in status
        assert "pubsub" in status
        assert "latency" in status

    def test_get_stats(self):
        stats = self.manager.get_stats()
        assert "cache" in stats
        assert "sessions" in stats

    def test_full_enterprise_stack(self):
        """Test all components working together."""
        # Cache
        self.manager.cache_set("ai:topic", {"name": "AI Trends"})
        cached = self.manager.cache_get("ai:topic")
        assert cached["name"] == "AI Trends"

        # Session
        session = self.manager.create_session("user1", "facebook", {"topic": "AI"})

        # Rate limit
        allowed, _ = self.manager.check_rate_limit("user1:generate", 10, 60)
        assert allowed is True

        # Pub/Sub
        events = []
        self.manager.subscribe_event("ai.events", lambda c, m, t, ts: events.append(m))
        self.manager.publish_event("ai.events", {"type": "post_generated"})

        # Queue
        task_id = self.manager.enqueue_task("publish", {"post_id": "123"})
        task = self.manager.dequeue_task()
        assert task["task_type"] == "publish"
        self.manager.get_queue().complete(task_id)

        # Verify
        assert len(events) == 1
        status = self.manager.get_redis_status()
        assert status["overall"] in ("Healthy", "Degraded")
