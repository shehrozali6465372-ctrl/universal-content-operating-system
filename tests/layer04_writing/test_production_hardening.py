import pytest

from layers.layer04_writing.modules.content_planner.writing_plan import WritingPlan
from layers.layer04_writing.modules.draft_generator.draft_manager import DraftManager
from layers.layer04_writing.modules.draft_generator.llm_provider import MockLLMProvider
from layers.layer04_writing.modules.draft_generator.prompt_builder import PromptBuilder
from layers.layer04_writing.modules.writing_memory.writing_memory import WritingMemory
from layers.layer04_writing.modules.writing_orchestrator.writing_orchestrator import WritingOrchestrator


def test_draft_variants_require_configured_provider():
    class Unconfigured(MockLLMProvider):
        def is_configured(self):
            return False
    manager = DraftManager(provider=Unconfigured())
    with pytest.raises(RuntimeError, match="not configured"):
        manager.generate_variants(WritingPlan("AI"))


def test_writing_memory_owns_input_lists_and_rejects_negative_tokens():
    personality = ["expert"]
    memory = WritingMemory()
    memory.set_voice("brand", personality=personality)
    personality.append("mutated")
    assert memory.get_voice("brand").personality == ["expert"]
    with pytest.raises(ValueError):
        memory.store_draft("facebook", "AI", "text", tokens=-1)


def test_prompt_builder_count_contract():
    builder = PromptBuilder()
    builder.build(WritingPlan("AI"))
    assert builder.prompt_count == 1


def test_orchestrator_generates_platform_local_hooks():
    orchestrator = WritingOrchestrator()
    result = orchestrator.run("AI", platforms=["facebook", "linkedin"])
    assert len(result.outputs) == 2
    assert all(output.hook for output in result.outputs)


def test_variant_validation_receives_platform():
    provider = MockLLMProvider(
        response="AI jobs are growing rapidly. Companies need skilled developers. "
                 "The market is changing quickly. More opportunities are appearing."
    )
    manager = DraftManager(provider=provider)
    plan = WritingPlan("AI jobs")
    plan.platform = "twitter"
    plan.length = "short"
    result = manager.generate_variants(plan, ["original"])
    assert result.variants[0].validation is not None


def test_import_plan_fails_closed_on_invalid_platform():
    from layers.layer04_writing.modules.content_planner.planner_manager import PlannerManager
    with pytest.raises(ValueError, match="failed validation"):
        PlannerManager().import_plan({"topic": "AI", "platform": "unknown"})
