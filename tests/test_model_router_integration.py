from layers.layer12_ai_foundation.modules.model_router.model_router import (
    ModelResponse,
    ModelRouter,
    RequestType,
)


def test_router_uses_registered_provider_and_records_success():
    router = ModelRouter()
    calls = []

    def handler(request):
        calls.append(request)
        return ModelResponse(request.request_id, "real provider output")

    router.register_provider("test", handler=handler, capabilities=[RequestType.TEXT])
    router.set_routing(RequestType.TEXT, ["test"])

    response = router.generate_text("hello", system_prompt="system")

    assert response.content == "real provider output"
    assert response.provider == "test"
    assert response.model_used == "test"
    assert len(calls) == 1
    assert calls[0].system_prompt == "system"
    assert router.get_stats()["success"] == 1


def test_router_rejects_empty_primary_and_uses_distinct_fallback():
    router = ModelRouter()
    calls = []

    def primary(request):
        calls.append("primary")
        return ModelResponse(request.request_id, "")

    def fallback(request):
        calls.append("fallback")
        return "fallback output"

    router.register_provider("primary", handler=primary, capabilities=[RequestType.TEXT])
    router.register_provider("fallback", handler=fallback, capabilities=[RequestType.TEXT])
    router.set_routing(RequestType.TEXT, ["primary", "fallback"])

    response = router.generate_text("hello")

    assert response.content == "fallback output"
    assert calls == ["primary", "fallback"]
    history = router.get_history()
    assert [item["status"] for item in history] == ["failed", "success"]


def test_router_does_not_claim_success_when_no_provider_can_respond():
    router = ModelRouter()
    router.register_provider("empty", handler=lambda request: "", capabilities=[RequestType.TEXT])
    router.set_routing(RequestType.TEXT, ["empty"])

    response = router.generate_text("hello")

    assert response.content == ""
    assert "empty" in response.metadata["error"]
    assert router.get_stats()["success"] == 0
    assert router.get_stats()["failed"] == 2


def test_router_fallback_does_not_call_primary_twice():
    router = ModelRouter()
    calls = {"primary": 0, "fallback": 0}

    def primary(request):
        calls["primary"] += 1
        raise RuntimeError("primary down")

    def fallback(request):
        calls["fallback"] += 1
        return "ok"

    router.register_provider("primary", handler=primary, capabilities=[RequestType.TEXT])
    router.register_provider("fallback", handler=fallback, capabilities=[RequestType.TEXT])
    router.set_routing(RequestType.TEXT, ["primary", "fallback"])

    assert router.generate_text("hello").content == "ok"
    assert calls == {"primary": 1, "fallback": 1}
