"""Tests for StateManager."""

from layers.layer02_research.modules.research_orchestrator.state_manager import StateManager
from layers.layer02_research.modules.research_orchestrator.exceptions import StateError


class TestStateManager:
    def setup_method(self):
        self.sm = StateManager()

    def test_can_transition_valid(self):
        assert self.sm.can_transition("created", "planned") is True

    def test_can_transition_invalid(self):
        assert self.sm.can_transition("created", "running") is False

    def test_transition_valid(self):
        new = self.sm.transition("created", "planned", "start")
        assert new == "planned"

    def test_transition_invalid_raises(self):
        try:
            self.sm.transition("created", "completed")
            assert False, "Should have raised"
        except StateError:
            pass

    def test_full_lifecycle(self):
        s = "created"
        s = self.sm.transition(s, "planned")
        assert s == "planned"
        s = self.sm.transition(s, "running")
        assert s == "running"
        s = self.sm.transition(s, "completed")
        assert s == "completed"

    def test_pause_resume(self):
        s = "created"
        s = self.sm.transition(s, "planned")
        s = self.sm.transition(s, "running")
        s = self.sm.transition(s, "paused")
        assert s == "paused"
        s = self.sm.transition(s, "resuming")
        assert s == "resuming"
        s = self.sm.transition(s, "running")
        assert s == "running"

    def test_failure_retry(self):
        s = "running"
        s = self.sm.transition(s, "failed")
        s = self.sm.transition(s, "retrying")
        assert s == "retrying"

    def test_cannot_transition_from_completed(self):
        assert self.sm.can_transition("completed", "running") is False

    def test_cannot_transition_from_cancelled(self):
        assert self.sm.can_transition("cancelled", "running") is False

    def test_is_terminal(self):
        assert self.sm.is_terminal("completed") is True
        assert self.sm.is_terminal("cancelled") is True
        assert self.sm.is_terminal("running") is False

    def test_is_active(self):
        assert self.sm.is_active("running") is True
        assert self.sm.is_active("paused") is True
        assert self.sm.is_active("completed") is False

    def test_history(self):
        self.sm.transition("created", "planned")
        self.sm.transition("planned", "running")
        history = self.sm.get_history()
        assert len(history) == 2
        assert history[0]["from"] == "created"
        assert history[0]["to"] == "planned"

    def test_last_transition(self):
        self.sm.transition("created", "planned")
        last = self.sm.get_last_transition()
        assert last["from"] == "created"
        assert last["to"] == "planned"

    def test_last_transition_empty(self):
        assert self.sm.get_last_transition() is None

    def test_reset(self):
        self.sm.transition("created", "planned")
        self.sm.reset()
        assert len(self.sm.get_history()) == 0
