"""Layer 20 production certification tests."""
from __future__ import annotations

import threading

import pytest

from layers.layer20_image_pipeline import (
    BatchGenerator,
    BatchStatus,
    CompositionEngine,
    CompositionRule,
    PromptBuilder,
    ProviderRouter,
    ProviderStatus,
    StyleEngine,
    StylePreset,
)


def test_prompt_builder_validates_and_serializes_complete_contract() -> None:
    builder = PromptBuilder()
    prompt = builder.build(
        "professional laptop",
        platform="Instagram",
        extra_tags=["marketing", "clean"],
    )
    builder.optimize_for_platform(prompt, "Pinterest")
    payload = prompt.to_dict()

    assert prompt.prompt_id.startswith("imgprompt_")
    assert payload["positive"].startswith("professional laptop")
    assert payload["platform"] == "pinterest"
    assert payload["parameters"]["aspect_ratio"] == "2:3"
    assert payload["parameters"]["quality"] == "high"
    assert payload["metadata"] == {}


def test_prompt_ids_are_unique() -> None:
    builder = PromptBuilder()
    ids = {builder.build("subject").prompt_id for _ in range(500)}
    assert len(ids) == 500


def test_prompt_template_is_fail_closed() -> None:
    builder = PromptBuilder()
    with pytest.raises(KeyError):
        builder.from_template("missing")

    builder.add_template("hero", "Create {subject} for {platform}")
    with pytest.raises(ValueError, match="template rendering failed"):
        builder.from_template("hero", subject="x")


def test_composition_rejects_unknown_layout_and_invalid_dimensions() -> None:
    engine = CompositionEngine()
    with pytest.raises(ValueError, match="unknown layout"):
        engine.create_plan("unknown")
    with pytest.raises(ValueError, match="positive"):
        engine.create_plan("center", (0, 1080))


def test_composition_validation_contains_rule_failures_and_exceptions() -> None:
    engine = CompositionEngine()
    plan = engine.create_plan("grid")
    rule = CompositionRule("must_have_element")
    rule.check_fn = lambda current: bool(current.elements)
    engine.add_rule(rule)
    result = engine.validate(plan)
    assert result["valid"] is False
    assert result["violations"] == ["must_have_element"]

    broken = CompositionRule("broken")
    broken.check_fn = lambda current: 1 / 0
    engine.add_rule(broken)
    result = engine.validate(plan)
    assert result["valid"] is False
    assert result["rule_errors"][0]["error_type"] == "ZeroDivisionError"


def test_composition_ids_are_unique_and_elements_validate() -> None:
    engine = CompositionEngine()
    plans = [engine.create_plan() for _ in range(200)]
    assert len({plan.plan_id for plan in plans}) == 200
    plans[0].add_element("image", (10, 20), (300, 200))
    assert plans[0].to_dict()["elements"] == 1
    with pytest.raises(ValueError):
        plans[0].add_element("", (0, 0), (1, 1))


def test_style_engine_does_not_alias_input_lists_or_content() -> None:
    colors = ["#fff"]
    preset = StylePreset("brand", colors=colors)
    colors.append("#000")
    assert preset.colors == ["#fff"]

    engine = StyleEngine()
    engine.add_preset(preset)
    source = {"title": "hello"}
    styled = engine.apply_style(source, "brand")
    assert source == {"title": "hello"}
    assert styled["style"]["colors"] == ["#fff"]
    assert styled is not source


def test_style_engine_validates_contracts() -> None:
    engine = StyleEngine()
    with pytest.raises(ValueError):
        StylePreset("")
    with pytest.raises(TypeError):
        engine.add_preset(object())  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        engine.apply_style([], "brand")  # type: ignore[arg-type]


def test_provider_router_fails_closed_without_handler() -> None:
    router = ProviderRouter()
    router.register("provider-a", cost_per_image=0.01)
    result = router.route({"positive": "test"})
    assert result == {
        "provider": "provider-a",
        "error": "provider_handler_not_configured",
    }


def test_provider_router_selects_and_records_latency() -> None:
    calls = []

    def handler(prompt):
        calls.append(prompt)
        return {"image_url": "https://example.invalid/image.png"}

    router = ProviderRouter()
    router.register("provider-a", handler=handler, cost_per_image=0.02)
    result = router.route({"positive": "test"})
    assert result["provider"] == "provider-a"
    assert result["result"]["image_url"].startswith("https://")
    assert result["latency_seconds"] >= 0
    assert calls == [{"positive": "test"}]
    assert router.history()[0]["provider"] == "provider-a"


def test_provider_router_quality_and_speed_require_telemetry() -> None:
    router = ProviderRouter()
    router.register("a", handler=lambda _: {"ok": True})
    assert router.route({}, "highest_quality")["error"] == "no_provider_quality_telemetry"
    assert router.route({}, "fastest")["error"] == "no_provider_speed_telemetry"

    with pytest.raises(ValueError):
        router.record_observation("a", quality_score=1.1)
    assert router.record_observation("a", quality_score=0.9, speed_score=0.8)
    assert router.route({}, "highest_quality")["provider"] == "a"


def test_provider_router_handler_exception_is_observable() -> None:
    def broken(_):
        raise RuntimeError("provider failed")

    router = ProviderRouter()
    router.register("broken", handler=broken)
    result = router.route({"positive": "test"})
    assert result["error_type"] == "RuntimeError"
    assert "provider failed" in result["error"]


def test_provider_router_status_and_input_contracts() -> None:
    router = ProviderRouter()
    router.register("a", handler=lambda _: {"ok": True})
    assert router.set_status("a", ProviderStatus.DISABLED)
    assert router.route({})["error"] == "no_available_provider"
    with pytest.raises(TypeError):
        router.route("not-a-dict")  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        router.route({}, "unsupported")


def test_batch_generator_fails_closed_without_generator() -> None:
    generator = BatchGenerator()
    job = generator.create_batch([{"prompt": "a"}])
    result = generator.execute_batch(job.batch_id)
    assert result["status"] == BatchStatus.FAILED.value
    assert result["errors"] == 1
    assert result["completed"] == 0


def test_batch_generator_requires_real_generator_and_is_idempotent() -> None:
    calls = []

    def generate(prompt):
        calls.append(prompt)
        return {"image_url": "memory://generated"}

    generator = BatchGenerator()
    generator.set_generator(generate)
    job = generator.create_batch([{"prompt": "a"}, {"prompt": "b"}])
    first = generator.execute_batch(job.batch_id)
    second = generator.execute_batch(job.batch_id)

    assert first["status"] == BatchStatus.COMPLETED.value
    assert first["completed"] == 2
    assert second == first
    assert len(calls) == 2


def test_batch_generator_rejects_invalid_results_and_preserves_partial_failure() -> None:
    def generate(prompt):
        if prompt["prompt"] == "bad":
            raise RuntimeError("generation failed")
        return {"image_url": "memory://ok"}

    generator = BatchGenerator()
    generator.set_generator(generate)
    job = generator.create_batch([{"prompt": "good"}, {"prompt": "bad"}])
    result = generator.execute_batch(job.batch_id)
    assert result["status"] == BatchStatus.FAILED.value
    assert result["completed"] == 1
    assert result["errors"] == 1
    assert generator.execute_batch(job.batch_id) == result


def test_batch_generator_ids_and_input_contract() -> None:
    generator = BatchGenerator()
    jobs = [generator.create_batch([{"prompt": str(i)}]) for i in range(200)]
    assert len({job.batch_id for job in jobs}) == 200
    with pytest.raises(TypeError):
        generator.create_batch(["invalid"])  # type: ignore[list-item]


def test_batch_generator_concurrent_execution_does_not_duplicate_work() -> None:
    calls = []
    lock = threading.Lock()

    def generate(prompt):
        with lock:
            calls.append(prompt)
        return {"ok": True}

    generator = BatchGenerator()
    generator.set_generator(generate)
    job = generator.create_batch([{"prompt": "one"}])
    results = []

    def execute():
        results.append(generator.execute_batch(job.batch_id))

    threads = [threading.Thread(target=execute) for _ in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert len(calls) == 1
    assert sum(result.get("error") == "batch_already_running" for result in results) >= 1
    assert generator.get_batch(job.batch_id).status == BatchStatus.COMPLETED


def test_cross_module_image_pipeline_contract() -> None:
    prompt = PromptBuilder().build("product hero", platform="instagram")
    composition = CompositionEngine().create_plan("center")
    composition.add_element("image", (0, 0), (1080, 1080))
    assert composition.validate(composition)["valid"]

    styles = StyleEngine()
    styles.add_preset(StylePreset("photorealistic", effects=["natural-light"]))
    content = styles.apply_style(prompt.to_dict(), "photorealistic")

    router = ProviderRouter()
    router.register("test-provider", handler=lambda payload: {"asset": payload})
    result = router.route(content)
    assert result["provider"] == "test-provider"
    assert result["result"]["asset"]["prompt_id"] == prompt.prompt_id
