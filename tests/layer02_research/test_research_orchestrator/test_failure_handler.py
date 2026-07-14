"""Tests for FailureHandler."""

from layers.layer02_research.modules.research_orchestrator.failure_handler import FailureHandler
from layers.layer02_research.modules.research_orchestrator.retry_coordinator import RetryPolicy


class TestFailureHandler:
    def setup_method(self):
        self.fh = FailureHandler(RetryPolicy(max_retries=3))

    def test_classify_timeout(self):
        assert self.fh.classify_error(TimeoutError("timed out")) == "timeout"

    def test_classify_api_error(self):
        assert self.fh.classify_error(ConnectionError("http failed")) == "api_error"

    def test_classify_data_error(self):
        assert self.fh.classify_error(ValueError("bad key")) == "data_error"

    def test_classify_unknown(self):
        assert self.fh.classify_error(RuntimeError("something")) == "unknown"

    def test_get_strategy(self):
        assert self.fh.get_strategy("timeout") == "retry"
        assert self.fh.get_strategy("data_error") == "skip"

    def test_is_retryable(self):
        assert self.fh.is_retryable("timeout") is True
        assert self.fh.is_retryable("data_error") is False

    def test_handle_failure_retryable(self):
        result = self.fh.handle_failure("m1", TimeoutError("timeout"))
        assert result["action"] == "retry"
        assert result["retryable"] is True

    def test_handle_failure_non_retryable(self):
        result = self.fh.handle_failure("m1", ValueError("bad data"))
        assert result["action"] == "skip"
        assert result["retryable"] is False

    def test_handle_failure_with_fallback(self):
        def fallback():
            return "fallback_result"
        result = self.fh.handle_failure("m1", ValueError("err"), fallback)
        assert result["action"] == "fallback"
        assert result["fallback_success"] is True

    def test_handle_failure_fallback_fails(self):
        def bad_fallback():
            raise RuntimeError("fallback also fails")
        result = self.fh.handle_failure("m1", ValueError("err"), bad_fallback)
        assert result["fallback_success"] is False

    def test_failure_log(self):
        self.fh.handle_failure("m1", ValueError("e"))
        log = self.fh.get_failure_log("m1")
        assert len(log) == 1

    def test_failure_log_all(self):
        self.fh.handle_failure("m1", ValueError("e"))
        self.fh.handle_failure("m2", ValueError("e"))
        assert len(self.fh.get_failure_log()) == 2

    def test_failure_counts(self):
        self.fh.handle_failure("m1", ValueError("e"))
        self.fh.handle_failure("m1", ValueError("e"))
        counts = self.fh.get_failure_counts()
        assert counts["m1"] == 2

    def test_most_failed_module(self):
        self.fh.handle_failure("m1", ValueError("e"))
        self.fh.handle_failure("m1", ValueError("e"))
        self.fh.handle_failure("m2", ValueError("e"))
        assert self.fh.get_most_failed_module() == "m1"

    def test_most_failed_empty(self):
        assert self.fh.get_most_failed_module() is None

    def test_reset(self):
        self.fh.handle_failure("m1", ValueError("e"))
        self.fh.reset()
        assert self.fh.get_failure_counts() == {}
