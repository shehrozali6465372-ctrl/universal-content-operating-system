"""Tests for GoalManager and ResearchGoal."""

from layers.layer02_research.modules.research_planner.goal_manager import GoalManager, ResearchGoal


class TestResearchGoal:
    def test_create_goal(self):
        g = ResearchGoal(title="Find trends")
        assert g.title == "Find trends"
        assert g.status == "pending"
        assert g.priority == "MEDIUM"

    def test_goal_id_unique(self):
        g1 = ResearchGoal(title="Goal A")
        g2 = ResearchGoal(title="Goal B")
        assert g1.goal_id != g2.goal_id

    def test_complete_goal(self):
        g = ResearchGoal(title="Test")
        g.complete(confidence=0.95)
        assert g.status == "completed"
        assert g.actual_confidence == 0.95
        assert g.completed_at != ""

    def test_fail_goal(self):
        g = ResearchGoal(title="Test")
        g.fail()
        assert g.status == "failed"

    def test_cancel_goal(self):
        g = ResearchGoal(title="Test")
        g.cancel()
        assert g.status == "cancelled"

    def test_is_achieved(self):
        g = ResearchGoal(title="Test", target_confidence=0.8)
        g.complete(confidence=0.9)
        assert g.is_achieved() is True

    def test_not_achieved_low_confidence(self):
        g = ResearchGoal(title="Test", target_confidence=0.9)
        g.complete(confidence=0.5)
        assert g.is_achieved() is False

    def test_not_achieved_not_completed(self):
        g = ResearchGoal(title="Test", target_confidence=0.5)
        assert g.is_achieved() is False

    def test_to_dict(self):
        g = ResearchGoal(title="Test", topic="AI", niche="tech")
        d = g.to_dict()
        assert d["title"] == "Test"
        assert d["topic"] == "AI"
        assert d["niche"] == "tech"
        assert "goal_id" in d

    def test_from_dict(self):
        data = {
            "title": "From Dict", "description": "desc",
            "topic": "crypto", "niche": "finance",
            "priority": "HIGH", "goal_id": "goal_123",
            "status": "completed", "actual_confidence": 0.88,
        }
        g = ResearchGoal.from_dict(data)
        assert g.title == "From Dict"
        assert g.topic == "crypto"
        assert g.goal_id == "goal_123"
        assert g.status == "completed"

    def test_invalid_priority_fallback(self):
        g = ResearchGoal(title="Test", priority="INVALID")
        assert g.priority == "MEDIUM"

    def test_clamp_confidence(self):
        g = ResearchGoal(title="Test", target_confidence=1.5)
        assert g.target_confidence == 1.0
        g2 = ResearchGoal(title="Test2", target_confidence=-0.5)
        assert g2.target_confidence == 0.0

    def test_parent_goal_id(self):
        g = ResearchGoal(title="Child", parent_goal_id="goal_parent_1")
        assert g.parent_goal_id == "goal_parent_1"


class TestGoalManager:
    def setup_method(self):
        self.manager = GoalManager()

    def test_create_goal(self):
        g = self.manager.create_goal("Find trends")
        assert g.title == "Find trends"
        assert self.manager.size() == 1

    def test_get_goal(self):
        g = self.manager.create_goal("Test")
        found = self.manager.get_goal(g.goal_id)
        assert found is not None
        assert found.title == "Test"

    def test_get_nonexistent_goal(self):
        assert self.manager.get_goal("nonexistent") is None

    def test_update_goal(self):
        g = self.manager.create_goal("Test")
        updated = self.manager.update_goal(g.goal_id, title="Updated")
        assert updated is not None
        assert updated.title == "Updated"

    def test_update_nonexistent_goal(self):
        result = self.manager.update_goal("nonexistent", title="X")
        assert result is None

    def test_complete_goal(self):
        g = self.manager.create_goal("Test")
        success = self.manager.complete_goal(g.goal_id, confidence=0.9)
        assert success is True
        assert g.status == "completed"

    def test_complete_nonexistent_goal(self):
        success = self.manager.complete_goal("nonexistent")
        assert success is False

    def test_list_goals(self):
        self.manager.create_goal("A", priority="HIGH")
        self.manager.create_goal("B", priority="LOW")
        all_goals = self.manager.list_goals()
        assert len(all_goals) == 2

    def test_list_goals_by_status(self):
        g1 = self.manager.create_goal("A")
        g2 = self.manager.create_goal("B")
        g1.complete()
        completed = self.manager.list_goals(status="completed")
        assert len(completed) == 1
        assert completed[0].goal_id == g1.goal_id

    def test_list_goals_by_priority(self):
        self.manager.create_goal("A", priority="HIGH")
        self.manager.create_goal("B", priority="HIGH")
        self.manager.create_goal("C", priority="LOW")
        highs = self.manager.list_goals(priority="HIGH")
        assert len(highs) == 2

    def test_get_pending(self):
        g1 = self.manager.create_goal("A")
        g2 = self.manager.create_goal("B")
        g1.complete()
        pending = self.manager.get_pending()
        assert len(pending) == 1

    def test_get_achieved(self):
        g = self.manager.create_goal("A", target_confidence=0.5)
        g.complete(confidence=0.8)
        achieved = self.manager.get_achieved()
        assert len(achieved) == 1

    def test_get_by_topic(self):
        self.manager.create_goal("A", topic="AI")
        self.manager.create_goal("B", topic="Crypto")
        self.manager.create_goal("C", topic="AI")
        ai_goals = self.manager.get_by_topic("AI")
        assert len(ai_goals) == 2

    def test_size(self):
        assert self.manager.size() == 0
        self.manager.create_goal("A")
        assert self.manager.size() == 1
