"""Tests for Layer 1: Core Intelligence"""

from layers.layer1_core.core import CoreIntelligence

class TestCoreIntelligence:
    def setup_method(self):
        self.core = CoreIntelligence()

    def test_initialization(self):
        assert self.core.name == "Core Intelligence Layer"
        assert self.core.version == "0.1.0"

    def test_think(self):
        result = self.core.think("test input")
        assert result is not None

    def test_plan(self):
        result = self.core.plan("test goal")
        assert result is not None

    def test_decide(self):
        result = self.core.decide(["option1", "option2"])
        assert result is not None
