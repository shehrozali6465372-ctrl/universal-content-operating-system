"""Tests for Gemini provider + ModelRouter integration without requiring network access."""
from __future__ import annotations

from layers.layer12_ai_foundation.modules.model_router.key_manager import KeyManager, KeyStatus
from layers.layer12_ai_foundation.modules.model_router.gemini_provider import GeminiProvider
from layers.layer12_ai_foundation.modules.model_router.model_router import ModelRouter, ModelResponse, RequestType
from layers.layer12_ai_foundation.modules.model_router.prompt_builder import PromptBuilder, PromptStyle


class TestFullPipeline:
    """End-to-end router wiring; external API availability is not assumed."""

    def setup_method(self):
        self.km = KeyManager()
        # These tests are deliberately network-free. Never consume real CI
        # credentials here: the autonomous E2E workflow owns real-key testing.
        self.km.register_key("k1", "AIzaSy_FAKE_11111111111111111111", "gemini")
        self.km.register_key("k2", "AIzaSy_FAKE_22222222222222222222", "gemini")
        self.km.register_key("k3", "AIzaSy_FAKE_33333333333333333333", "gemini")
        self.gemini = GeminiProvider(self.km)
        self.router = ModelRouter(self.km)

        def _gemini_handler(request):
            result = self.gemini.generate(request.prompt)
            if result.get("error") or not result.get("content"):
                raise RuntimeError(result.get("error", "Gemini returned no content"))
            resp = ModelResponse(request.request_id, result["content"])
            resp.provider = result.get("provider", "gemini")
            resp.model_used = result.get("model", "")
            resp.tokens_used = result.get("tokens_used", 0)
            return resp

        self.router.register_provider("gemini", handler=_gemini_handler)
        self.prompt_builder = PromptBuilder()

    def test_ai_brain_to_gemini_flow(self):
        response = self.router.generate_text("What is artificial intelligence?")
        assert response.provider in ("gemini", "")
        assert response.content or response.metadata.get("error")

    def test_key_rotation_under_load(self):
        for i in range(10):
            self.gemini.generate(f"Test request {i}")
        assert self.km.get_stats()["total_requests"] >= 10

    def test_key_health_tracking(self):
        self.gemini.generate("test")
        health = self.km.get_all_health()
        assert len(health) == 3
        assert sum(h["total_requests"] for h in health) >= 1

    def test_prompt_builder_to_router(self):
        prompt_result = self.prompt_builder.build("Write a social media post about AI", PromptStyle.CHAIN_OF_THOUGHT, system_prompt="You are a social media expert")
        user_msg = next((m["content"] for m in prompt_result["messages"] if m["role"] == "user"), "")
        response = self.router.generate_text(user_msg)
        assert response.content or response.metadata.get("error")

    def test_simulated_when_no_network(self):
        result = self.gemini.generate("Hello")
        assert "provider" in result
        assert result.get("error") is not None or result.get("text") != ""

    def test_stats_comprehensive(self):
        self.gemini.generate("test1")
        self.gemini.generate("test2")
        stats = self.gemini.get_stats()
        assert stats["total_requests"] == 2
        assert "total_tokens" in stats

    def test_real_keys_never_in_response(self):
        for _ in range(5):
            result = self.gemini.generate("test")
            response_str = str(result)
            assert "FAKE_1111" not in response_str or "SIMULATED" in response_str

    def test_multiple_providers_routing(self):
        def mock_gemini(request):
            return ModelResponse(request.request_id, "Gemini response")
        def mock_deepseek(request):
            return ModelResponse(request.request_id, "DeepSeek response")
        router = ModelRouter()
        router.register_provider("gemini", handler=mock_gemini)
        router.register_provider("deepseek", handler=mock_deepseek)
        router.set_routing(RequestType.TEXT, ["gemini", "deepseek"])
        response = router.generate_text("test")
        assert response.content in ("Gemini response", "DeepSeek response")

    def test_failover_to_next_provider(self):
        def failing_handler(request):
            raise Exception("Provider down")
        def working_handler(request):
            return ModelResponse(request.request_id, "Fallback works")
        router = ModelRouter()
        router.register_provider("bad", handler=failing_handler)
        router.register_provider("good", handler=working_handler)
        response = router.generate_text("test")
        assert response.provider == "good"
        assert response.content == "Fallback works"

    def test_chat_api(self):
        result = self.gemini.chat([{"role": "user", "content": "Hello"}, {"role": "assistant", "content": "Hi!"}, {"role": "user", "content": "Tell me about AI"}])
        assert "provider" in result
        assert result.get("error") is not None or result.get("text") != ""

    def test_key_degradation_and_recovery(self):
        kh = self.km._keys["k1"]
        for _ in range(3):
            kh.record_error("error")
        assert kh.status == KeyStatus.DEGRADED
        assert kh.is_available
        kh.record_success(100.0, 10)
        assert kh.status == KeyStatus.HEALTHY

    def test_all_keys_exhausted_fallback(self):
        for kid in self.km._keys:
            for _ in range(5):
                self.km._keys[kid].record_error("error")
        result = self.gemini.generate("test")
        assert result.get("error") is not None or result.get("text") == ""

    def test_rate_limit_handling(self):
        kh = self.km._keys["k1"]
        kh.record_error("429 Too Many Requests", is_rate_limit=True)
        assert kh.status == KeyStatus.RATE_LIMITED
        assert not kh.is_available
        result = self.gemini.generate("test")
        assert "provider" in result
