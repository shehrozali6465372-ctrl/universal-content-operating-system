"""Tests for Layer 6 Module 8 — Human Review & Approval Engine."""
from layers.layer06_quality.modules.human_review_engine.review_models import ReviewRequest, ReviewComment, AuditEntry
from layers.layer06_quality.modules.human_review_engine.workflow_manager import WorkflowManager
from layers.layer06_quality.modules.human_review_engine.confidence_router import ConfidenceRouter
from layers.layer06_quality.modules.human_review_engine.review_manager import ReviewManager


# ── ReviewModels Tests ──

class TestReviewModels:
    def test_review_comment(self):
        c = ReviewComment(comment_id=1, reviewer="Alice", text="Fix this", severity="warning")
        d = c.to_dict()
        assert d["reviewer"] == "Alice"
        assert d["severity"] == "warning"

    def test_audit_entry(self):
        e = AuditEntry(action="transition", actor="Bob", from_stage="draft", to_stage="review")
        d = e.to_dict()
        assert d["action"] == "transition"
        assert d["from_stage"] == "draft"

    def test_review_request(self):
        r = ReviewRequest(request_id=1, content="Test content", title="Test", author="Alice")
        assert r.current_stage == "draft"
        d = r.to_dict()
        assert "request_id" in d


# ── WorkflowManager Tests ──

class TestWorkflowManager:
    def setup_method(self):
        self.wf = WorkflowManager()

    def test_valid_transition(self):
        assert self.wf.can_transition("draft", "review")
        assert self.wf.can_transition("review", "approved")
        assert self.wf.can_transition("approved", "scheduled")
        assert self.wf.can_transition("scheduled", "published")

    def test_invalid_transition(self):
        assert not self.wf.can_transition("draft", "published")
        assert not self.wf.can_transition("published", "review")

    def test_review_to_draft(self):
        assert self.wf.can_transition("review", "draft")

    def test_transition_success(self):
        req = ReviewRequest(request_id=1, content="Test")
        success, msg = self.wf.transition(req, "review", actor="Alice")
        assert success
        assert req.current_stage == "review"

    def test_transition_failure(self):
        req = ReviewRequest(request_id=1, content="Test")
        success, msg = self.wf.transition(req, "published", actor="Alice")
        assert not success

    def test_audit_log_recorded(self):
        req = ReviewRequest(request_id=1, content="Test")
        self.wf.transition(req, "review", actor="Alice", reason="Submitted")
        assert len(req.audit_log) == 1
        assert req.audit_log[0].action == "transition"

    def test_get_valid_transitions(self):
        transitions = self.wf.get_valid_transitions("draft")
        assert "review" in transitions

    def test_get_stage_history(self):
        req = ReviewRequest(request_id=1, content="Test")
        self.wf.transition(req, "review")
        self.wf.transition(req, "approved")
        history = self.wf.get_stage_history(req)
        assert len(history) == 2

    def test_transition_count(self):
        req = ReviewRequest(request_id=1, content="Test")
        self.wf.transition(req, "review")
        assert self.wf.transition_count == 1


# ── ConfidenceRouter Tests ──

class TestConfidenceRouter:
    def setup_method(self):
        self.router = ConfidenceRouter()

    def test_high_confidence_auto_approve(self):
        req = ReviewRequest(request_id=1, content="Test")
        req.confidence_score = 0.95
        decision = self.router.route(req)
        assert decision.action == "auto_approve"
        assert not decision.requires_human

    def test_medium_confidence_review(self):
        req = ReviewRequest(request_id=1, content="Test")
        req.confidence_score = 0.7
        decision = self.router.route(req)
        assert decision.action == "review"
        assert decision.requires_human

    def test_low_confidence_escalate(self):
        req = ReviewRequest(request_id=1, content="Test")
        req.confidence_score = 0.3
        decision = self.router.route(req)
        assert decision.action == "escalate"
        assert decision.escalation_level >= 1

    def test_high_risk_escalate(self):
        req = ReviewRequest(request_id=1, content="Test")
        req.confidence_score = 0.95
        req.risk_category = "medical"
        decision = self.router.route(req)
        assert decision.action == "escalate"
        assert decision.escalation_level >= 2

    def test_route_batch(self):
        requests = [
            ReviewRequest(request_id=i, content="Test") for i in range(3)
        ]
        requests[0].confidence_score = 0.95
        requests[1].confidence_score = 0.7
        requests[2].confidence_score = 0.3
        decisions = self.router.route_batch(requests)
        assert len(decisions) == 3

    def test_get_auto_approvable(self):
        requests = [ReviewRequest(request_id=1, content="Test")]
        requests[0].confidence_score = 0.95
        decisions = self.router.route_batch(requests)
        auto = self.router.get_auto_approvable(decisions)
        assert len(auto) == 1

    def test_to_dict(self):
        req = ReviewRequest(request_id=1, content="Test")
        req.confidence_score = 0.8
        decision = self.router.route(req)
        d = decision.to_dict()
        assert "action" in d
        assert "confidence" in d

    def test_route_count(self):
        req = ReviewRequest(request_id=1, content="Test")
        self.router.route(req)
        assert self.router.route_count == 1


# ── ReviewManager Tests ──

class TestReviewManager:
    def setup_method(self):
        self.manager = ReviewManager()

    def test_create_request(self):
        req = self.manager.create_request(
            content="AI technology post.", title="AI Post", author="Alice"
        )
        assert req.request_id == 1
        assert req.current_stage == "draft"

    def test_submit_for_review(self):
        req = self.manager.create_request(content="Test", author="Alice")
        success, msg = self.manager.submit_for_review(req.request_id, actor="Alice")
        assert success
        assert req.current_stage == "review"

    def test_approve(self):
        req = self.manager.create_request(content="Test", author="Alice")
        self.manager.submit_for_review(req.request_id)
        success, msg = self.manager.approve(req.request_id, reviewer="Bob", comment="Looks good")
        assert success
        assert req.current_approvals == 1

    def test_reject(self):
        req = self.manager.create_request(content="Test", author="Alice")
        self.manager.submit_for_review(req.request_id)
        success, msg = self.manager.reject(req.request_id, reviewer="Bob", reason="Needs revision")
        assert success
        assert req.current_stage == "draft"

    def test_schedule_and_publish(self):
        req = self.manager.create_request(content="Test", author="Alice")
        self.manager.submit_for_review(req.request_id)
        self.manager.approve(req.request_id, reviewer="Bob")
        self.manager.schedule(req.request_id)
        assert req.current_stage == "scheduled"
        self.manager.publish(req.request_id)
        assert req.current_stage == "published"

    def test_add_comment(self):
        req = self.manager.create_request(content="Test", author="Alice")
        comment = self.manager.add_comment(
            req.request_id, reviewer="Bob", text="Fix tone",
            severity="warning", position_start=10, position_end=20,
        )
        assert comment is not None
        assert comment.reviewer == "Bob"
        assert len(req.comments) == 1

    def test_add_comment_nonexistent(self):
        comment = self.manager.add_comment(999, "Bob", "Fix")
        assert comment is None

    def test_get_request(self):
        req = self.manager.create_request(content="Test")
        found = self.manager.get_request(req.request_id)
        assert found is not None

    def test_get_by_stage(self):
        self.manager.create_request(content="Draft 1")
        req2 = self.manager.create_request(content="Draft 2")
        self.manager.submit_for_review(req2.request_id)
        drafts = self.manager.get_by_stage("draft")
        reviews = self.manager.get_by_stage("review")
        assert len(drafts) == 1
        assert len(reviews) == 1

    def test_get_pending_review(self):
        req = self.manager.create_request(content="Test")
        self.manager.submit_for_review(req.request_id)
        pending = self.manager.get_pending_review()
        assert len(pending) == 1

    def test_statistics(self):
        self.manager.create_request(content="Test 1")
        req2 = self.manager.create_request(content="Test 2")
        self.manager.submit_for_review(req2.request_id)
        stats = self.manager.get_statistics()
        assert stats["total_requests"] == 2
        assert stats["by_stage"]["draft"] == 1
        assert stats["by_stage"]["review"] == 1

    def test_full_lifecycle(self):
        req = self.manager.create_request(content="AI post", author="Alice")
        self.manager.submit_for_review(req.request_id, actor="Alice")
        self.manager.add_comment(req.request_id, "Bob", "Looks good", "info")
        self.manager.approve(req.request_id, reviewer="Bob")
        self.manager.schedule(req.request_id, actor="Alice")
        self.manager.publish(req.request_id, actor="Alice")
        assert req.current_stage == "published"
        assert len(req.audit_log) >= 5

    def test_check_count(self):
        self.manager.create_request(content="Test")
        assert self.manager.check_count == 1
