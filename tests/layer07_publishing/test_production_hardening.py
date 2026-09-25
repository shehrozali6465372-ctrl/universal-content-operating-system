"""Focused production-hardening regression tests for Layer 7."""

import time

from layers.layer07_publishing.modules.publisher_engine.publish_transaction import (
    PublishTransaction,
)
from layers.layer07_publishing.modules.failure_recovery.circuit_breaker import (
    CircuitBreaker,
    STATE_OPEN,
)


def test_publish_transaction_executes_callables_and_rolls_back_completed_steps():
    rolled_back = []
    txn = PublishTransaction("tx-prod-1")
    txn.add_step("prepare", lambda: True,
                  lambda: (rolled_back.append("prepare"), True)[1])
    txn.add_step("publish", lambda: False,
                  lambda: (rolled_back.append("publish"), True)[1])

    assert txn.execute() is False
    assert txn.is_completed is False
    assert txn.is_rolled_back is True
    assert rolled_back == ["prepare"]
    assert txn.get_steps()[1]["executed"] is False


def test_publish_transaction_is_single_use():
    txn = PublishTransaction("tx-prod-2")
    txn.add_step("publish", lambda: True)
    assert txn.execute() is True
    try:
        txn.execute()
    except RuntimeError:
        return
    raise AssertionError("transaction allowed a second execution")


def test_circuit_breaker_allows_only_one_half_open_probe():
    breaker = CircuitBreaker(
        failure_threshold=2,
        recovery_timeout=0.01,
        success_threshold=2,
    )
    breaker.record_failure("facebook")
    breaker.record_failure("facebook")
    assert breaker.get_state("facebook") == STATE_OPEN
    time.sleep(0.02)

    assert breaker.can_execute("facebook") is True
    assert breaker.can_execute("facebook") is False
    breaker.record_failure("facebook")
    assert breaker.get_state("facebook") == STATE_OPEN
