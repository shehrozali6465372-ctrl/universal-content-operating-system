"""Tests for RetryCoordinator."""

from layers.layer02_research.modules.research_orchestrator.retry_coordinator import (
    RetryCoordinator, RetryPolicy, RetryAttempt,
)
from layers.layer02_research.modules.research_orchestrator.exceptions import RetryExhaustedError


class TestRetryPolicy:
    def test_default_policy(self):
        p = RetryPolicy()
        assert p.max_retries == 3
        assert p.backoff_multiplier == 2.0

    def test_custom_policy(self):
        p = RetryPolicy(max_retries=5, base_delay_sec=0.5)
        assert p.max_retries == 5
        assert p.base_delay_sec == 0.5

    def test_to_dict(self):
        d = RetryPolicy().to_dict()
        assert "max_retries" in d


class TestRetryAttempt:
    def test_create_attempt(self):
        a = RetryAttempt(1, "m1", "timeout")
        assert a.attempt_number == 1
        assert a.module == "m1"
        assert a.error == "timeout"

    def test_to_dict(self):
        d = RetryAttempt(2, "m1", "err", 1.5).to_dict()
        assert d["attempt_number"] == 2
        assert d["delay_sec"] == 1.5


class TestRetryCoordinator:
    def setup_method(self):
        self.rc = RetryCoordinator(RetryPolicy(max_retries=3))

    def test_should_retry_initial(self):
        assert self.rc.should_retry("m1") is True

    def test_should_retry_after_max(self):
        for _ in range(3):
            self.rc.record_attempt("m1", "error")
        assert self.rc.should_retry("m1") is False

    def test_record_attempt(self):
        a = self.rc.record_attempt("m1", "timeout")
        assert a.attempt_number == 1
        assert a.module == "m1"

    def test_get_delay(self):
        delay = self.rc.get_delay("m1")
        assert delay > 0

    def test_get_attempts(self):
        self.rc.record_attempt("m1", "e1")
        self.rc.record_attempt("m1", "e2")
        attempts = self.rc.get_attempts("m1")
        assert len(attempts) == 2

    def test_get_total_retries(self):
        self.rc.record_attempt("m1", "e")
        self.rc.record_attempt("m2", "e")
        assert self.rc.get_total_retries() == 2

    def test_reset_module(self):
        self.rc.record_attempt("m1", "e")
        self.rc.reset_module("m1")
        assert self.rc.should_retry("m1") is True

    def test_reset_all(self):
        self.rc.record_attempt("m1", "e")
        self.rc.record_attempt("m2", "e")
        self.rc.reset_all()
        assert self.rc.get_total_retries() == 0

    def test_execute_with_retry_success(self):
        def ok():
            return "success"
        result = self.rc.execute_with_retry("m1", ok)
        assert result == "success"

    def test_execute_with_retry_exhausted(self):
        def fail():
            raise ValueError("always fails")
        try:
            self.rc.execute_with_retry("m1", fail)
            assert False, "Should have raised"
        except RetryExhaustedError:
            pass
