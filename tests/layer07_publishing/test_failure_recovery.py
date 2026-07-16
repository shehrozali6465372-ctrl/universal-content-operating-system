"""Tests for Layer 7 Module 6 — Failure Recovery Engine."""
import time
from layers.layer07_publishing.modules.failure_recovery.failure_detector import (
    FailureDetector, FailureRecord, ERROR_TYPES, SEVERITY_LEVELS,
)
from layers.layer07_publishing.modules.failure_recovery.error_classifier import (
    ErrorClassifier, ErrorClassification, RETRYABLE, PERMANENT, PLATFORM_SPECIFIC,
)
from layers.layer07_publishing.modules.failure_recovery.retry_strategy import (
    RetryStrategy, RetryPolicy, RetryAttempt, POLICY_EAGER, POLICY_NORMAL, POLICY_PATIENT, POLICY_RATE_LIMIT,
)
from layers.layer07_publishing.modules.failure_recovery.circuit_breaker import (
    CircuitBreaker, STATE_CLOSED, STATE_OPEN, STATE_HALF_OPEN,
)
from layers.layer07_publishing.modules.failure_recovery.rollback_manager import (
    RollbackManager,
)
from layers.layer07_publishing.modules.failure_recovery.recovery_actions import (
    RecoveryActions, RecoveryAction,
)
from layers.layer07_publishing.modules.failure_recovery.incident_logger import (
    IncidentLogger,
)
from layers.layer07_publishing.modules.failure_recovery.recovery_metrics import RecoveryMetrics
from layers.layer07_publishing.modules.failure_recovery.failure_memory import (
    FailureMemory,
)
from layers.layer07_publishing.modules.failure_recovery.recovery_manager import (
    RecoveryManager, RecoveryResult,
)
from layers.layer07_publishing.modules.failure_recovery.exceptions import (
    RecoveryError, CircuitOpenError, RecoveryExhaustedError, RollbackFailedError,
)


# ─── FailureDetector Tests ───────────────────────────────────────────
class TestFailureRecord:
    def test_create(self):
        r = FailureRecord("network", "Connection timeout")
        assert r.failure_id.startswith("fail_")
        assert r.error_type == "network"
        assert r.message == "Connection timeout"

    def test_create_unknown(self):
        r = FailureRecord("bogus_type", "error")
        assert r.error_type == "unknown"

    def test_to_dict(self):
        r = FailureRecord("auth", "Unauthorized")
        d = r.to_dict()
        assert d["error_type"] == "auth"
        assert d["severity"] == "medium"
        assert "timestamp" in d

    def test_constants(self):
        assert "network" in ERROR_TYPES
        assert "low" in SEVERITY_LEVELS


class TestFailureDetector:
    def setup_method(self):
        self.detector = FailureDetector()

    def test_detect_timeout(self):
        r = self.detector.detect_from_exception(TimeoutError("connection timeout"), "facebook")
        assert r.error_type == "network"
        assert r.platform == "facebook"

    def test_detect_auth_error(self):
        r = self.detector.detect_from_exception(Exception("Unauthorized access"))
        assert r.error_type == "auth"

    def test_detect_rate_limit(self):
        r = self.detector.detect_from_exception(Exception("Rate limit exceeded"))
        assert r.error_type == "rate_limit"

    def test_detect_upload_error(self):
        r = self.detector.detect_from_exception(Exception("Upload failed: file too large"))
        assert r.error_type == "media"

    def test_detect_content_error(self):
        r = self.detector.detect_from_exception(Exception("Content violates policy"))
        assert r.error_type == "content"

    def test_detect_unknown(self):
        r = self.detector.detect_from_exception(Exception("Something weird"))
        assert r.error_type == "unknown"

    def test_detect_from_response_with_error(self):
        resp = {"error": "Rate limited"}
        r = self.detector.detect_from_response(resp, "linkedin")
        assert r is not None
        assert r.error_type == "rate_limit"

    def test_detect_from_response_no_error(self):
        assert self.detector.detect_from_response({}) is None

    def test_detect_from_response_dict_error(self):
        resp = {"error": {"message": "Unauthorized"}}
        r = self.detector.detect_from_response(resp)
        assert r is not None
        assert r.error_type == "auth"

    def test_detect_from_status_code_429(self):
        r = self.detector.detect_from_status_code(429)
        assert r.error_type == "rate_limit"
        assert r.severity == "high"

    def test_detect_from_status_code_401(self):
        r = self.detector.detect_from_status_code(401)
        assert r.error_type == "auth"

    def test_detect_from_status_code_500(self):
        r = self.detector.detect_from_status_code(500)
        assert r.error_type == "api"

    def test_detect_from_status_code_404(self):
        r = self.detector.detect_from_status_code(404)
        assert r.error_type == "platform"

    def test_detection_count(self):
        self.detector.detect_from_exception(Exception("error"))
        self.detector.detect_from_status_code(500)
        assert self.detector.detection_count == 2


# ─── ErrorClassifier Tests ───────────────────────────────────────────
class TestErrorClassifier:
    def setup_method(self):
        self.classifier = ErrorClassifier()

    def test_classify_retryable_network(self):
        record = FailureRecord("network", "Connection timeout")
        cls = self.classifier.classify(record)
        assert cls.category == RETRYABLE
        assert cls.retryable is True
        assert "retry" in cls.suggested_action or "immediate" in cls.suggested_action

    def test_classify_retryable_rate_limit(self):
        record = FailureRecord("rate_limit", "Rate limit exceeded")
        cls = self.classifier.classify(record)
        assert cls.category == RETRYABLE
        assert cls.retryable is True
        assert cls.suggested_action == "wait_and_retry"

    def test_classify_permanent_auth(self):
        record = FailureRecord("auth", "Unauthorized")
        cls = self.classifier.classify(record)
        assert cls.category == PERMANENT
        assert cls.retryable is False
        assert cls.suggested_action == "refresh_token"

    def test_classify_permanent_content(self):
        record = FailureRecord("content", "Violates policy")
        cls = self.classifier.classify(record)
        assert cls.category == PERMANENT
        assert cls.retryable is False

    def test_classify_platform(self):
        record = FailureRecord("platform", "Not found")
        cls = self.classifier.classify(record)
        assert cls.category == PLATFORM_SPECIFIC

    def test_classify_unknown(self):
        record = FailureRecord("unknown", "???")
        cls = self.classifier.classify(record)
        assert cls.category == "unknown"
        assert cls.retryable is False

    def test_is_retryable(self):
        record = FailureRecord("api", "Server error")
        assert self.classifier.is_retryable(record) is True

    def test_classify_batch(self):
        records = [
            FailureRecord("network", "timeout"),
            FailureRecord("auth", "unauthorized"),
        ]
        results = self.classifier.classify_batch(records)
        assert len(results) == 2
        assert results[0].retryable is True
        assert results[1].retryable is False

    def test_classification_count(self):
        self.classifier.classify(FailureRecord("network", "err"))
        self.classifier.classify(FailureRecord("auth", "err"))
        assert self.classifier.classification_count == 2

    def test_confidence_rate_limit(self):
        cls = self.classifier.classify(FailureRecord("rate_limit", "429"))
        assert cls.confidence >= 0.9

    def test_confidence_unknown(self):
        cls = self.classifier.classify(FailureRecord("unknown", "???"))
        assert cls.confidence < 0.6


# ─── RetryStrategy Tests ─────────────────────────────────────────────
class TestRetryPolicy:
    def test_default_policy(self):
        p = RetryPolicy()
        assert p.max_retries == 3
        assert p.base_delay == 1.0

    def test_to_dict(self):
        p = RetryPolicy(max_retries=5)
        d = p.to_dict()
        assert d["max_retries"] == 5

    def test_presets(self):
        assert POLICY_EAGER.max_retries == 1
        assert POLICY_NORMAL.max_retries == 3
        assert POLICY_PATIENT.max_retries == 5
        assert POLICY_RATE_LIMIT.base_delay == 10.0


class TestRetryAttempt:
    def test_to_dict(self):
        a = RetryAttempt(1, 2.0)
        d = a.to_dict()
        assert d["attempt"] == 1
        assert d["delay"] == 2.0


class TestRetryStrategy:
    def setup_method(self):
        self.strategy = RetryStrategy()

    def test_should_retry(self):
        assert self.strategy.should_retry(0) is True
        assert self.strategy.should_retry(2) is True
        assert self.strategy.should_retry(3) is False

    def test_get_delay_increases(self):
        d0 = self.strategy.get_delay(0)
        d1 = self.strategy.get_delay(1)
        assert d1 >= d0

    def test_get_delay_capped(self):
        p = RetryPolicy(max_delay=5.0)
        s = RetryStrategy(p)
        assert s.get_delay(100) <= 5.0

    def test_get_total_delay(self):
        total = self.strategy.get_total_delay(3)
        assert total > 0

    def test_record_attempt(self):
        rec = self.strategy.record_attempt(0, "timeout")
        assert rec.attempt == 0
        assert rec.error == "timeout"

    def test_record_attempt_success(self):
        rec = self.strategy.record_attempt(1, success=True)
        assert rec.success is True

    def test_get_history(self):
        self.strategy.record_attempt(0, "err")
        history = self.strategy.get_history()
        assert len(history) == 1

    def test_reset_history(self):
        self.strategy.record_attempt(0)
        self.strategy.reset_history()
        assert self.strategy.total_attempts == 0

    def test_eager_policy_no_jitter(self):
        s = RetryStrategy(POLICY_EAGER)
        d1 = s.get_delay(0)
        d2 = s.get_delay(0)
        assert d1 == d2  # no jitter


# ─── CircuitBreaker Tests ────────────────────────────────────────────
class TestCircuitBreaker:
    def setup_method(self):
        self.cb = CircuitBreaker(failure_threshold=3, recovery_timeout=1.0)

    def test_initial_state_closed(self):
        assert self.cb.can_execute("api1") is True
        assert self.cb.get_state("api1") == STATE_CLOSED

    def test_opens_after_threshold(self):
        for _ in range(3):
            self.cb.record_failure("api1")
        assert self.cb.get_state("api1") == STATE_OPEN

    def test_blocks_when_open(self):
        for _ in range(3):
            self.cb.record_failure("api1")
        assert self.cb.can_execute("api1") is False

    def test_transitions_to_half_open_after_timeout(self):
        for _ in range(3):
            self.cb.record_failure("api1")
        time.sleep(1.1)
        assert self.cb.can_execute("api1") is True
        assert self.cb.get_state("api1") == STATE_HALF_OPEN

    def test_closes_after_success_in_half_open(self):
        for _ in range(3):
            self.cb.record_failure("api1")
        time.sleep(1.1)
        self.cb.can_execute("api1")
        for _ in range(2):
            self.cb.record_success("api1")
        assert self.cb.get_state("api1") == STATE_CLOSED

    def test_reopens_on_failure_in_half_open(self):
        for _ in range(3):
            self.cb.record_failure("api1")
        time.sleep(1.1)
        self.cb.can_execute("api1")  # → half_open
        self.cb.record_failure("api1")
        assert self.cb.get_state("api1") == STATE_OPEN

    def test_success_resets_count_in_closed(self):
        self.cb.record_failure("api1")
        self.cb.record_success("api1")
        assert self.cb.get_state("api1") == STATE_CLOSED

    def test_get_all_states(self):
        self.cb.record_failure("api1")
        states = self.cb.get_all_states()
        assert "api1" in states

    def test_reset(self):
        for _ in range(3):
            self.cb.record_failure("api1")
        self.cb.reset("api1")
        assert self.cb.get_state("api1") == STATE_CLOSED

    def test_reset_all(self):
        self.cb.record_failure("api1")
        self.cb.reset_all()
        assert self.cb.circuit_count == 0

    def test_open_circuits(self):
        for _ in range(3):
            self.cb.record_failure("api1")
        assert "api1" in self.cb.open_circuits


# ─── RollbackManager Tests ───────────────────────────────────────────
class TestRollbackManager:
    def setup_method(self):
        self.rb = RollbackManager()

    def test_add_action(self):
        action = self.rb.add_action("delete_post", lambda: True)
        assert action.executed is True
        assert self.rb.action_count == 1

    def test_execute_rollback(self):
        rolled = []
        self.rb.add_action("step1", lambda: (rolled.append("s1"), True)[1])
        self.rb.add_action("step2", lambda: (rolled.append("s2"), True)[1])
        result = self.rb.execute_rollback()
        assert result["success"] is True
        assert rolled == ["s2", "s1"]  # reversed

    def test_rollback_failure(self):
        self.rb.add_action("bad", lambda: False)
        result = self.rb.execute_rollback()
        assert result["success"] is False

    def test_rollback_exception(self):
        def boom():
            raise RuntimeError("rollback crashed")
        self.rb.add_action("crash", boom)
        result = self.rb.execute_rollback()
        assert result["success"] is False

    def test_get_actions(self):
        self.rb.add_action("s1", lambda: True)
        actions = self.rb.get_actions()
        assert len(actions) == 1
        assert actions[0]["name"] == "s1"

    def test_rollback_count(self):
        self.rb.add_action("s1", lambda: True)
        self.rb.execute_rollback()
        assert self.rb.rollback_count == 1

    def test_undo_media(self):
        assert self.rb.undo_published_media(["m1", "m2"]) is True

    def test_restore_state(self):
        assert self.rb.restore_previous_state({"key": "val"}) is True


# ─── RecoveryActions Tests ────────────────────────────────────────────
class TestRecoveryAction:
    def test_create(self):
        a = RecoveryAction("refresh_token", "Refresh the token")
        assert a.action_type == "refresh_token"
        assert a.priority == 5

    def test_execute_with_fn(self):
        a = RecoveryAction("retry_immediate", "retry", executable=lambda: True)
        assert a.execute() is True

    def test_execute_without_fn(self):
        a = RecoveryAction("delay_publish", "delay")
        assert a.execute() is True

    def test_execute_exception(self):
        a = RecoveryAction("retry_immediate", "r", executable=lambda: (_ for _ in ()).throw(RuntimeError))
        assert a.execute() is False

    def test_to_dict(self):
        a = RecoveryAction("switch_endpoint", "switch")
        d = a.to_dict()
        assert d["action_type"] == "switch_endpoint"

    def test_invalid_type(self):
        a = RecoveryAction("bogus", "test")
        assert a.action_type == "retry_immediate"


class TestRecoveryActions:
    def test_suggest_for_rate_limit(self):
        record = FailureRecord("rate_limit", "429")
        cls = ErrorClassification(RETRYABLE)
        actions = RecoveryActions.suggest_actions(record, cls)
        assert len(actions) >= 1
        assert any(a.action_type in ("retry_exponential", "delay_publish") for a in actions)

    def test_suggest_for_auth(self):
        record = FailureRecord("auth", "unauthorized")
        cls = ErrorClassification(PERMANENT)
        actions = RecoveryActions.suggest_actions(record, cls)
        assert any(a.action_type == "refresh_token" for a in actions)

    def test_suggest_for_network(self):
        record = FailureRecord("network", "timeout")
        cls = ErrorClassification(RETRYABLE)
        actions = RecoveryActions.suggest_actions(record, cls)
        assert any(a.action_type == "retry_immediate" for a in actions)

    def test_suggest_for_platform(self):
        record = FailureRecord("platform", "not found")
        cls = ErrorClassification(PLATFORM_SPECIFIC)
        actions = RecoveryActions.suggest_actions(record, cls)
        assert any(a.action_type == "force_resync" for a in actions)

    def test_suggest_for_unknown(self):
        record = FailureRecord("unknown", "???")
        cls = ErrorClassification("unknown")
        actions = RecoveryActions.suggest_actions(record, cls)
        assert len(actions) >= 1

    def test_get_recommended(self):
        record = FailureRecord("rate_limit", "429")
        cls = ErrorClassification(RETRYABLE)
        action = RecoveryActions.get_recommended_action(record, cls)
        assert isinstance(action, RecoveryAction)

    def test_priorities_set(self):
        record = FailureRecord("network", "timeout")
        cls = ErrorClassification(RETRYABLE)
        actions = RecoveryActions.suggest_actions(record, cls)
        priorities = [a.priority for a in actions]
        assert priorities == sorted(priorities)


# ─── IncidentLogger Tests ────────────────────────────────────────────
class TestIncidentLogger:
    def setup_method(self):
        self.logger = IncidentLogger()

    def test_log_incident(self):
        record = FailureRecord("network", "timeout")
        entry = self.logger.log_incident(record)
        assert entry.incident_id.startswith("INC-")
        assert self.logger.incident_count == 1

    def test_incident_entry_timeline(self):
        record = FailureRecord("auth", "unauthorized")
        entry = self.logger.log_incident(record)
        entry.add_event("retrying", "attempt 1")
        assert len(entry.timeline) == 2  # detected + retrying

    def test_mark_resolved(self):
        record = FailureRecord("rate_limit", "429")
        entry = self.logger.log_incident(record)
        entry.mark_resolved()
        assert entry.resolved is True

    def test_get_incidents_filter(self):
        self.logger.log_incident(FailureRecord("network", "t", platform="fb"))
        self.logger.log_incident(FailureRecord("auth", "a", platform="li"))
        assert len(self.logger.get_incidents(platform="fb")) == 1

    def test_get_unresolved(self):
        entry1 = self.logger.log_incident(FailureRecord("network", "e"))
        entry2 = self.logger.log_incident(FailureRecord("auth", "e"))
        entry1.mark_resolved()
        unresolved = self.logger.get_unresolved()
        assert len(unresolved) == 1

    def test_get_stats(self):
        self.logger.log_incident(FailureRecord("network", "e"))
        self.logger.log_incident(FailureRecord("auth", "e"))
        stats = self.logger.get_stats()
        assert stats["total"] == 2
        assert "network" in stats["by_type"]

    def test_incident_to_dict(self):
        record = FailureRecord("media", "upload failed")
        entry = self.logger.log_incident(record)
        d = entry.to_dict()
        assert "incident_id" in d
        assert d["error_type"] == "media"

    def test_incident_entry_context(self):
        record = FailureRecord("network", "e")
        entry = self.logger.log_incident(record)
        entry.context["attempt"] = 3
        assert entry.context["attempt"] == 3


# ─── RecoveryMetrics Tests ────────────────────────────────────────────
class TestRecoveryMetrics:
    def setup_method(self):
        self.metrics = RecoveryMetrics()

    def test_record_failure_recovered(self):
        self.metrics.record_failure(True, 100.0)
        snap = self.metrics.get_current()
        assert snap["recovered"] == 1
        assert snap["failed"] == 0

    def test_record_failure_not_recovered(self):
        self.metrics.record_failure(False, 200.0)
        snap = self.metrics.get_current()
        assert snap["failed"] == 1

    def test_record_retry(self):
        self.metrics.record_retry()
        self.metrics.record_retry()
        snap = self.metrics.get_current()
        assert snap["total_retries"] == 2

    def test_recovery_rate(self):
        self.metrics.record_failure(True, 50)
        self.metrics.record_failure(True, 50)
        self.metrics.record_failure(False, 50)
        snap = self.metrics.get_current()
        assert snap["recovery_rate"] > 0.6

    def test_take_snapshot(self):
        self.metrics.record_failure(True, 100)
        snap = self.metrics.take_snapshot()
        assert len(self.metrics.get_snapshots()) == 1

    def test_reset(self):
        self.metrics.record_failure(True, 100)
        self.metrics.reset()
        snap = self.metrics.get_current()
        assert snap["total_failures"] == 0


# ─── FailureMemory Tests ──────────────────────────────────────────────
class TestFailureMemory:
    def setup_method(self):
        self.memory = FailureMemory()

    def test_observe(self):
        record = FailureRecord("network", "timeout", platform="facebook")
        pat = self.memory.observe(record, recovered=True)
        assert pat.count == 1
        assert pat.error_type == "network"

    def test_observe_increments(self):
        record = FailureRecord("rate_limit", "429", platform="facebook")
        self.memory.observe(record, recovered=True)
        self.memory.observe(record, recovered=False)
        pat = self.memory.get_pattern("rate_limit", "facebook")
        assert pat is not None
        assert pat.count == 2

    def test_success_rate(self):
        record = FailureRecord("network", "t", platform="fb")
        self.memory.observe(record, recovered=True)
        self.memory.observe(record, recovered=True)
        pat = self.memory.get_pattern("network", "fb")
        assert pat.success_rate == 1.0

    def test_get_recurring(self):
        record = FailureRecord("api", "err", platform="fb")
        for _ in range(5):
            self.memory.observe(record)
        recurring = self.memory.get_recurring(min_count=3)
        assert len(recurring) >= 1

    def test_get_best_strategy(self):
        record = FailureRecord("network", "t", platform="fb")
        self.memory.observe(record, recovered=True)
        self.memory.observe(record, recovered=True)
        self.memory.update_best_recovery("network", "fb", "immediate_retry")
        strategy = self.memory.get_best_strategy("network", "fb")
        assert strategy == "immediate_retry"

    def test_get_best_strategy_default(self):
        strategy = self.memory.get_best_strategy("unknown_type")
        assert strategy == "retry_exponential"

    def test_get_all_patterns(self):
        self.memory.observe(FailureRecord("network", "t", platform="fb"))
        self.memory.observe(FailureRecord("auth", "a", platform="li"))
        patterns = self.memory.get_all_patterns()
        assert len(patterns) == 2

    def test_get_stats(self):
        self.memory.observe(FailureRecord("network", "t", platform="fb"))
        stats = self.memory.get_stats()
        assert stats["total_patterns"] == 1
        assert "fb" in stats["platforms"]

    def test_pattern_to_dict(self):
        record = FailureRecord("rate_limit", "429", platform="fb")
        pat = self.memory.observe(record)
        d = pat.to_dict()
        assert "pattern_id" in d
        assert d["error_type"] == "rate_limit"

    def test_pattern_count(self):
        self.memory.observe(FailureRecord("network", "t", platform="fb"))
        assert self.memory.pattern_count == 1


# ─── RecoveryManager Tests ────────────────────────────────────────────
class TestRecoveryResult:
    def test_create(self):
        r = RecoveryResult()
        assert r.success is False
        assert r.final_status == "failed"

    def test_to_dict(self):
        r = RecoveryResult()
        r.success = True
        r.recovered = True
        d = r.to_dict()
        assert d["success"] is True
        assert d["recovered"] is True


class TestRecoveryManager:
    def setup_method(self):
        self.manager = RecoveryManager()

    def test_handle_failure_retryable(self):
        record = FailureRecord("network", "Connection timeout")
        counter = [0]
        def publish_fn():
            counter[0] += 1
            return counter[0] >= 2
        result = self.manager.handle_failure(record, publish_fn, "facebook", "r1")
        assert result.recovered is True
        assert result.attempts >= 1

    def test_handle_failure_permanent(self):
        record = FailureRecord("auth", "Unauthorized")
        result = self.manager.handle_failure(record, lambda: False, "linkedin")
        assert result.recovered is False

    def test_handle_exception(self):
        result = self.manager.handle_exception(
            TimeoutError("Connection timed out"),
            lambda: True,
            "facebook",
        )
        assert result.success is True or result.recovered is True

    def test_handle_response_with_error(self):
        resp = {"error": "Rate limit exceeded"}
        counter = [0]
        def publish_fn():
            counter[0] += 1
            return counter[0] >= 1
        result = self.manager.handle_response(resp, publish_fn, "twitter")
        assert result.success is True or result.recovered is True

    def test_handle_response_no_error(self):
        result = self.manager.handle_response({}, lambda: True, "facebook")
        assert result.success is True

    def test_circuit_breaker_integration(self):
        record = FailureRecord("network", "timeout", platform="fb")
        for _ in range(10):
            self.manager.handle_failure(record, lambda: False, "fb")
        assert self.manager.circuit_breaker.get_state("fb_network") == STATE_OPEN

    def test_failure_memory_integration(self):
        record = FailureRecord("rate_limit", "429", platform="fb")
        self.manager.handle_failure(record, lambda: True, "fb")
        pat = self.manager.failure_memory.get_pattern("rate_limit", "fb")
        assert pat is not None
        assert pat.count >= 1

    def test_incident_logged(self):
        record = FailureRecord("auth", "Unauthorized")
        self.manager.handle_failure(record, lambda: False, "fb")
        assert self.manager.incident_logger.incident_count >= 1

    def test_metrics_recorded(self):
        record = FailureRecord("network", "timeout")
        self.manager.handle_failure(record, lambda: True, "fb")
        snap = self.manager.metrics.get_current()
        assert snap["total_failures"] >= 1

    def test_events_tracked(self):
        record = FailureRecord("network", "timeout")
        self.manager.handle_failure(record, lambda: True, "fb")
        assert len(self.manager.events) >= 1

    def test_recovery_count(self):
        record = FailureRecord("network", "timeout")
        self.manager.handle_failure(record, lambda: True, "fb")
        assert self.manager.recovery_count == 1

    def test_handle_failure_all_exhausted(self):
        record = FailureRecord("network", "timeout")
        result = self.manager.handle_failure(record, lambda: False, "fb")
        assert result.recovered is False
        assert result.action in ("retry_exhausted", "retry_success")


# ─── Exceptions Tests ────────────────────────────────────────────────
class TestExceptions:
    def test_hierarchy(self):
        assert issubclass(RecoveryError, Exception)
        assert issubclass(CircuitOpenError, RecoveryError)
        assert issubclass(RecoveryExhaustedError, RecoveryError)
        assert issubclass(RollbackFailedError, RecoveryError)

    def test_message(self):
        err = RecoveryError("test error")
        assert str(err) == "test error"

    def test_catch_as_base(self):
        try:
            raise CircuitOpenError("circuit open")
        except RecoveryError:
            pass
