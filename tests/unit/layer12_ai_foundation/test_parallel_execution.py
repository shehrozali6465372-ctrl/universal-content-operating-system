"""Regression tests for fail-closed, genuinely concurrent model execution."""
import threading

import pytest

from layers.layer12_ai_foundation.modules.multi_model_intelligence.models import ModelResponse
from layers.layer12_ai_foundation.modules.multi_model_intelligence.parallel_generation import ParallelGeneration
from layers.layer12_ai_foundation.modules.multi_model_intelligence.parallel_review import ParallelReview
from layers.layer12_ai_foundation.modules.multi_model_intelligence.parallel_reasoning import ParallelReasoning


@pytest.mark.parametrize(
    ("runner", "method", "payload"),
    [
        (ParallelGeneration(), "generate", "prompt"),
        (ParallelReasoning(), "reason", "prompt"),
        (ParallelReview(), "review", "content"),
    ],
)
def test_parallel_model_operations_refuse_missing_provider_callback(runner, method, payload):
    with pytest.raises(ValueError, match="real provider callback"):
        getattr(runner, method)(payload, ["model-a"])


def test_parallel_generation_calls_provider_concurrently_and_preserves_input_order():
    barrier = threading.Barrier(3)

    def call(prompt, model):
        barrier.wait(timeout=2)
        return ModelResponse(model=model, provider="test", content=f"result:{model}")

    results = ParallelGeneration(max_parallel=3).generate(
        "write", ["model-a", "model-b", "model-c"], call_fn=call
    )
    assert [result.model for result in results] == ["model-a", "model-b", "model-c"]
    assert [result.content for result in results] == [
        "result:model-a", "result:model-b", "result:model-c"
    ]


def test_parallel_review_never_fabricates_positive_reviews():
    def fail(content, reviewer):
        raise RuntimeError("review provider unavailable")

    results = ParallelReview(max_concurrent=2).review(
        "article", ["critic-a", "critic-b"], call_fn=fail
    )
    assert len(results) == 2
    assert all(not result.is_success for result in results)
    assert all("review provider unavailable" in result.error for result in results)
