import pytest

from layers.layer13_persistence.modules.postgresql.connection.pool import (
    ConnectionConfig,
    ConnectionPool,
)


def test_connection_config_rejects_invalid_pool_bounds():
    with pytest.raises(ValueError, match="min_connections"):
        ConnectionConfig(min_connections=4, max_connections=2)


def test_connection_config_rejects_non_positive_retry_attempts():
    with pytest.raises(ValueError, match="max_retries"):
        ConnectionConfig(max_retries=0)


def test_insert_rejects_empty_payload_before_database_access():
    pool = ConnectionPool(ConnectionConfig())
    with pytest.raises(ValueError, match="non-empty dictionary"):
        pool.insert("config", {})


def test_insert_many_rejects_mismatched_columns_before_database_access():
    pool = ConnectionPool(ConnectionConfig())
    with pytest.raises(ValueError, match="identical columns"):
        pool.insert_many(
            "config",
            [{"key": "a", "value": "1"}, {"key": "b"}],
        )


def test_pool_latency_metrics_are_bounded_and_accumulated():
    pool = ConnectionPool(ConnectionConfig())
    for value in range(pool._MAX_LATENCY_SAMPLES + 25):
        pool._query_latencies.append(float(value))
        pool._total_latency_ms += float(value)
    metrics = pool.get_pool_metrics()
    assert metrics["latency"]["samples"] == pool._MAX_LATENCY_SAMPLES
    assert metrics["latency"]["total_latency_ms"] == pytest.approx(
        sum(pool._query_latencies), rel=0, abs=1e-9
    )
