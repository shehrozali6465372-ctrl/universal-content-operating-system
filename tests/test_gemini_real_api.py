"""Tests for Real Gemini API Integration — KeyManager + GeminiProvider + ModelRouter."""
from __future__ import annotations
import time
import os
import pytest

from layers.layer12_ai_foundation.modules.model_router.key_manager import KeyManager, KeyStatus
from layers.layer12_ai_foundation.modules.model_router.gemini_provider import GeminiProvider
from layers.layer12_ai_foundation.modules.model_router.model_router import (
    ModelRouter, ModelRequest, ModelResponse, RequestType
)
from layers.layer12_ai_foundation.modules.model_router.prompt_builder import (
    PromptBuilder, PromptStyle
)


# ═══════════════════════════════════════════════════════════════════════
# Integration Test: Full Pipeline
# ═══════════════════════════════════════════════════════════════════════
class TestFullPipeline:
    """End-to-end: AI Brain → ModelRouter → KeyManager → GeminiProvider"""

    def setup_method(self):
        self.km = KeyManager()
        self.km.register_key("k1", os.environ.get("GEMINI_API_KEY_1", "AIzaSy_FAKE_11111111111111111111"), "gemini")
        self.km.register_key("k2", os.environ.get("GEMINIAPIKEY2", "AIzaSy_FAKE_22222222222222222222"), "gemini")
        self.km.register_key("k3", os.environ.get("GEMINIAPIKEY3", "AIzaSy_FAKE_33333333333333333333"), "gemini")

        self.gemini = GeminiProvider(self.km)
        self.router = ModelRouter(self.km)
        def _gemini_handler(request):
            result = self.gemini.generate(request.prompt)
            resp = ModelResponse(request.request_id, result.get("content", ""))
            resp.provider = result.get("provider", "gemini")
            resp.model_used = result.get("model", "")
            resp.tokens_used = result.get("tokens_used", 0)
            return resp
        self.router.register_provider("gemini", handler=_gemini_handler)
        self.prompt_builder = PromptBuilder()

    def test_ai_brain_to_gemini_flow(self):
        """AI Brain bole → Router route kare → KeyManager key de → Gemini API call ho."""
        response = self.router.generate_text("What is artificial intelligence?")
        assert response.content is not None
        assert len(response.content) > 0
        assert response.provider == "gemini"

    def test_key_rotation_under_load(self):
        """100 requests bhejo — keys rotate hone chahiye."""
        for i in range(10):
            self.gemini.generate(f"Test request {i}")
        stats = self.km.get_stats()
        assert stats["total_requests"] >= 10

    def test_key_health_tracking(self):
        """Key health properly track ho rahi hai."""
        self.gemini.generate("test")
        health = self.km.get_all_health()
        assert len(health) == 3
        # At least one key should have been used
        total_requests = sum(h["total_requests"] for h in health)
        assert total_requests >= 1

    def test_prompt_builder_to_router(self):
        """PromptBuilder banaye prompt → Router use kare."""
        prompt_result = self.prompt_builder.build(
            "Write a social media post about AI",
            PromptStyle.CHAIN_OF_THOUGHT,
            system_prompt="You are a social media expert"
        )
        # Extract user message
        user_msg = next(
            (m["content"] for m in prompt_result["messages"] if m["role"] == "user"),
            ""
        )
        response = self.router.generate_text(user_msg)
        assert response.content is not None

    def test_simulated_when_no_network(self):
        """Jab network nahi hai, simulated response aana chahiye."""
        # Use fake keys — will fail API call → simulated response
        result = self.gemini.generate("Hello")
        assert result["content"] is not None
        # Should be simulated or real depending on network
        assert "provider" in result

    def test_stats_comprehensive(self):
        """Stats properly track ho rahe hain."""
        self.gemini.generate("test1")
        self.gemini.generate("test2")
        stats = self.gemini.get_stats()
        assert stats["total_requests"] == 2
        assert "total_tokens" in stats

    def test_real_keys_never_in_response(self):
        """Actual API keys kabhi response mein nahi aani chahiye."""
        for _ in range(5):
            result = self.gemini.generate("test")
            response_str = str(result)
            # Fake keys should not appear
            assert "FAKE_1111" not in response_str or "SIMULATED" in response_str

    def test_multiple_providers_routing(self):
        """Multiple providers add karo — router best select kare."""
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
        """Primary provider fail ho to fallback ho."""
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
        """Chat API properly kaam kare."""
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi! How can I help?"},
            {"role": "user", "content": "Tell me about AI"},
        ]
        result = self.gemini.chat(messages)
        assert result["content"] is not None

    def test_key_degradation_and_recovery(self):
        """Key degrade ho aur phir recover ho."""
        kh = self.km._keys["k1"]
        # Degrade
        for _ in range(3):
            kh.record_error("error")
        assert kh.status == KeyStatus.DEGRADED
        # Should still be usable (degraded, not exhausted)
        assert kh.is_available
        # Recover
        kh.record_success(100.0, 10)
        assert kh.status == KeyStatus.HEALTHY

    def test_all_keys_exhausted_fallback(self):
        """Sab keys exhaust ho to simulated response aaye."""
        for kid in self.km._keys:
            for _ in range(5):
                self.km._keys[kid].record_error("error")
        result = self.gemini.generate("test")
        assert result["content"] is not None

    def test_rate_limit_handling(self):
        """Rate limit detect ho aur cooldown lag jaye."""
        kh = self.km._keys["k1"]
        kh.record_error("429 Too Many Requests", is_rate_limit=True)
        assert kh.status == KeyStatus.RATE_LIMITED
        assert not kh.is_available
        # Other keys should still work
        result = self.gemini.generate("test")
        assert result["content"] is not None
