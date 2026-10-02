import json

from layers.layer12_ai_foundation.modules.model_router.deepseek_provider import DeepSeekProvider
from layers.layer12_ai_foundation.modules.model_router.key_manager import KeyManager
from layers.layer12_ai_foundation.modules.model_router.model_router import ModelRouter, RequestType


def test_key_manager_filters_credentials_by_provider():
    manager = KeyManager()
    manager.register_key("gemini-1", "gemini-secret", "gemini")
    manager.register_key("deepseek-1", "deepseek-secret", "deepseek")

    key_id, key = manager.select_key_with_id("text", provider="deepseek")
    assert key_id == "deepseek-1"
    assert key == "deepseek-secret"


def test_deepseek_provider_uses_key_manager_and_parses_response(monkeypatch):
    manager = KeyManager()
    manager.register_key("deepseek-1", "deepseek-secret", "deepseek")

    class FakeResponse:
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False
        def read(self):
            return json.dumps({
                "model": "deepseek-flash",
                "choices": [{"message": {"content": "UCOS_DEEPSEEK_OK"}}],
                "usage": {"total_tokens": 7},
            }).encode()

    def fake_urlopen(request, timeout):
        assert request.full_url.endswith("/chat/completions")
        assert request.headers["Authorization"] == "Bearer deepseek-secret"
        return FakeResponse()

    monkeypatch.setattr(
        "layers.layer12_ai_foundation.modules.model_router.deepseek_provider.urllib.request.urlopen",
        fake_urlopen,
    )

    result = DeepSeekProvider(manager).generate("hello")
    assert result["content"] == "UCOS_DEEPSEEK_OK"
    assert result["provider"] == "deepseek"
    assert result["model"] == "deepseek-flash"
    assert manager.get_stats()["total_requests"] == 1


def test_router_accepts_deepseek_as_text_provider():
    router = ModelRouter()
    router.register_provider("deepseek", handler=lambda request: "deepseek output",
                             capabilities=[RequestType.TEXT])
    router.set_routing(RequestType.TEXT, ["deepseek"])

    response = router.generate_text("hello")
    assert response.provider == "deepseek"
    assert response.content == "deepseek output"
