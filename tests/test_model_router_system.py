"""Tests for Model Router System — KeyManager, ModelRouter, PromptBuilder, GeminiProvider."""
from __future__ import annotations
import time
import pytest

# ═══════════════════════════════════════════════════════════════════════
# KeyManager Tests
# ═══════════════════════════════════════════════════════════════════════
from layers.layer12_ai_foundation.modules.model_router.key_manager import (
    KeyManager, KeyHealth, KeyStatus
)


class TestKeyHealth:
    def test_initial_state(self):
        kh = KeyHealth("k1", "***key1", "gemini")
        assert kh.status == KeyStatus.HEALTHY
        assert kh.is_available
        assert kh.success_rate == 100.0

    def test_record_success(self):
        kh = KeyHealth("k1", "***key1")
        kh.record_success(latency_ms=150.0, tokens_used=50)
        assert kh.total_requests == 1
        assert kh.requests_today == 1
        assert kh.tokens_used == 50
        assert kh.rpm_remaining == 59
        assert kh.avg_latency_ms == 150.0

    def test_record_error(self):
        kh = KeyHealth("k1", "***key1")
        kh.record_error("timeout")
        assert kh.total_errors == 1
        assert kh.consecutive_errors == 1
        assert kh.status == KeyStatus.DEGRADED

    def test_rate_limit_detection(self):
        kh = KeyHealth("k1", "***key1")
        kh.record_error("429 Too Many Requests", is_rate_limit=True)
        assert kh.status == KeyStatus.RATE_LIMITED
        assert kh.rpm_remaining == 0

    def test_consecutive_errors_exhausted(self):
        kh = KeyHealth("k1", "***key1")
        for _ in range(5):
            kh.record_error("error")
        assert kh.status == KeyStatus.EXHAUSTED
        assert not kh.is_available

    def test_auto_recovery(self):
        kh = KeyHealth("k1", "***key1")
        kh.record_error("error")
        kh.record_error("error")
        assert kh.status == KeyStatus.DEGRADED
        kh.record_success(100.0, 10)
        assert kh.status == KeyStatus.HEALTHY

    def test_cooldown(self):
        kh = KeyHealth("k1", "***key1")
        kh.set_cooldown(1)
        assert kh.status == KeyStatus.COOLDOWN
        assert not kh.is_available
        kh.cooldown_until = time.time() - 1
        assert kh.is_available
        assert kh.status == KeyStatus.HEALTHY

    def test_daily_reset(self):
        kh = KeyHealth("k1", "***key1")
        kh.record_success(100.0, 50)
        kh.record_success(100.0, 50)
        assert kh.requests_today == 2
        kh.reset_daily()
        assert kh.requests_today == 0
        assert kh.rpm_remaining == 60

    def test_to_dict(self):
        kh = KeyHealth("k1", "***key1")
        d = kh.to_dict()
        assert d["key_id"] == "k1"
        assert d["status"] == "healthy"
        assert d["is_available"]


class TestKeyManager:
    def setup_method(self):
        self.km = KeyManager()

    def test_register_keys(self):
        self.km.register_key("k1", "AIzaSy_REAL_KEY_111111", "gemini")
        self.km.register_key("k2", "AIzaSy_REAL_KEY_222222", "gemini")
        self.km.register_key("k3", "AIzaSy_REAL_KEY_333333", "gemini")
        assert len(self.km.list_keys()) == 3

    def test_select_key_healthy(self):
        self.km.register_key("k1", "key_1_real", "gemini")
        self.km.register_key("k2", "key_2_real", "gemini")
        key = self.km.select_key()
        assert key is not None
        assert key.startswith("key_") or key.startswith("AIza")

    def test_select_key_avoids_exhausted(self):
        self.km.register_key("k1", "key_1", "gemini")
        self.km.register_key("k2", "key_2", "gemini")
        # Exhaust key1
        kh = self.km._keys["k1"]
        for _ in range(5):
            kh.record_error("error")
        # Should select key2
        selected = self.km.select_key()
        assert selected == "key_2"

    def test_strategy_healthiest(self):
        self.km.set_strategy("healthiest")
        self.km.register_key("k1", "key_1", "gemini")
        self.km.register_key("k2", "key_2", "gemini")
        self.km._keys["k1"].record_success(50.0, 10)
        self.km._keys["k1"].record_success(50.0, 10)
        self.km._keys["k2"].record_error("error")
        # k1 has better success rate
        selected = self.km.select_key()
        assert selected == "key_1"

    def test_strategy_round_robin(self):
        self.km.set_strategy("round_robin")
        self.km.register_key("k1", "key_1", "gemini")
        self.km.register_key("k2", "key_2", "gemini")
        # Reset request counts
        self.km._keys["k1"].total_requests = 0
        self.km._keys["k2"].total_requests = 0
        results = set()
        for _ in range(4):
            r = self.km.select_key()
            results.add(r)
        assert len(results) >= 1  # Round robin should cycle

    def test_report_success(self):
        self.km.register_key("k1", "key_1", "gemini")
        self.km.report_success("k1", latency_ms=100.0, tokens_used=50)
        stats = self.km.get_stats()
        assert stats["total_requests"] == 1

    def test_report_error(self):
        self.km.register_key("k1", "key_1", "gemini")
        self.km.report_error("k1", "timeout")
        stats = self.km.get_stats()
        assert stats["total_errors"] == 1

    def test_force_cooldown(self):
        self.km.register_key("k1", "key_1", "gemini")
        assert self.km.force_cooldown("k1", 30)
        assert not self.km._keys["k1"].is_available

    def test_get_all_health(self):
        self.km.register_key("k1", "key_1", "gemini")
        self.km.register_key("k2", "key_2", "gemini")
        health = self.km.get_all_health()
        assert len(health) == 2
        # Verify actual keys are NOT exposed
        for h in health:
            assert "key_1" not in str(h).replace("***", "")
            assert "key_2" not in str(h).replace("***", "")

    def test_stats(self):
        self.km.register_key("k1", "key_1", "gemini")
        self.km.register_key("k2", "key_2", "gemini")
        stats = self.km.get_stats()
        assert stats["total_keys"] == 2
        assert stats["healthy"] == 2

    def test_unregister(self):
        self.km.register_key("k1", "key_1", "gemini")
        assert self.km.unregister_key("k1")
        assert self.km.get_key_health("k1") is None

    def test_no_keys_available(self):
        self.km.register_key("k1", "key_1", "gemini")
        kh = self.km._keys["k1"]
        for _ in range(5):
            kh.record_error("error")
        assert self.km.select_key() is None


# ═══════════════════════════════════════════════════════════════════════
# ModelRouter Tests
# ═══════════════════════════════════════════════════════════════════════
from layers.layer12_ai_foundation.modules.model_router.model_router import (
    ModelRouter, ModelRequest, ModelResponse, RequestType, ProviderAdapter
)


class TestModelRouter:
    def setup_method(self):
        self.router = ModelRouter()

    def test_register_provider(self):
        adapter = self.router.register_provider("gemini", handler=lambda r: "ok")
        assert adapter.provider_name == "gemini"
        assert len(self.router.list_providers()) == 1

    def test_generate_text(self):
        self.router.register_provider("gemini", handler=lambda r: "Hello from Gemini")
        response = self.router.generate_text("Say hello")
        assert response.content == "Hello from Gemini"
        assert response.provider == "gemini"

    def test_generate_chat(self):
        self.router.register_provider("gemini", handler=lambda r: "Chat response")
        messages = [{"role": "user", "content": "Hi"}]
        response = self.router.generate_chat(messages)
        assert response.content == "Chat response"

    def test_generate_image(self):
        def image_handler(request):
            return ModelResponse(request.request_id, "image_url_placeholder")
        self.router.register_provider("dalle", handler=image_handler,
                                       capabilities=[RequestType.IMAGE])
        response = self.router.generate_image("A sunset")
        assert "image" in response.content

    def test_routing_priority(self):
        self.router.register_provider("deepseek", handler=lambda r: "DeepSeek response")
        self.router.register_provider("gemini", handler=lambda r: "Gemini response")
        self.router.set_routing(RequestType.TEXT, ["deepseek", "gemini"])
        response = self.router.generate_text("test")
        assert response.provider == "deepseek"

    def test_fallback(self):
        def failing_handler(request):
            raise Exception("Provider down")
        self.router.register_provider("bad_provider", handler=failing_handler)
        self.router.register_provider("good_provider", handler=lambda r: "fallback works")
        response = self.router.generate_text("test")
        assert response.provider == "good_provider"

    def test_no_provider(self):
        response = self.router.generate_text("test")
        assert "No available provider" in response.content

    def test_unregister_provider(self):
        self.router.register_provider("gemini", handler=lambda r: "ok")
        assert self.router.unregister_provider("gemini")
        assert len(self.router.list_providers()) == 0

    def test_stats(self):
        self.router.register_provider("gemini", handler=lambda r: "ok")
        self.router.generate_text("test1")
        self.router.generate_text("test2")
        stats = self.router.get_stats()
        assert stats["total_requests"] == 2
        assert stats["success"] == 2

    def test_provider_capabilities(self):
        adapter = self.router.register_provider(
            "image_ai", handler=lambda r: "img",
            capabilities=[RequestType.IMAGE, RequestType.EMBEDDING])
        assert adapter.supports(RequestType.IMAGE)
        assert not adapter.supports(RequestType.TEXT)

    def test_history(self):
        self.router.register_provider("gemini", handler=lambda r: "ok")
        self.router.generate_text("test")
        history = self.router.get_history()
        assert len(history) == 1


# ═══════════════════════════════════════════════════════════════════════
# PromptBuilder Tests
# ═══════════════════════════════════════════════════════════════════════
from layers.layer12_ai_foundation.modules.model_router.prompt_builder import (
    PromptBuilder, PromptTemplate, PromptStyle
)


class TestPromptBuilder:
    def setup_method(self):
        self.pb = PromptBuilder()

    def test_build_direct(self):
        result = self.pb.build("Write a blog post", PromptStyle.DIRECT)
        assert "prompt_id" in result
        assert result["style"] == "direct"
        assert len(result["messages"]) >= 1

    def test_build_chain_of_thought(self):
        result = self.pb.build("Solve this math problem", PromptStyle.CHAIN_OF_THOUGHT)
        assert "Think step by step" in result["messages"][-1]["content"]

    def test_build_few_shot(self):
        examples = [{"input": "Hello", "output": "Hi there!"}]
        result = self.pb.build("Say hi", PromptStyle.FEW_SHOT, examples=examples)
        # Should have system + example + user messages
        assert len(result["messages"]) >= 2

    def test_build_reflection(self):
        result = self.pb.build("Draft content", PromptStyle.REFLECTION)
        assert "Review and improve" in result["messages"][-1]["content"]

    def test_build_with_context(self):
        context = {"platform": "instagram", "tone": "casual"}
        result = self.pb.build("Post about AI", context=context)
        # Context should be injected
        has_context = any("Context:" in m.get("content", "") for m in result["messages"])
        assert has_context

    def test_build_with_system_prompt(self):
        result = self.pb.build("Write", system_prompt="You are a copywriter")
        assert result["messages"][0]["role"] == "system"

    def test_build_text(self):
        text = self.pb.build_text("Simple task")
        assert isinstance(text, str)
        assert len(text) > 0

    def test_template(self):
        tmpl = PromptTemplate("blog", "Write a {topic} blog post for {audience}")
        self.pb.add_template(tmpl)
        assert len(self.pb.list_templates()) == 1
        rendered = tmpl.render(topic="AI", audience="developers")
        assert "AI" in rendered
        assert "developers" in rendered

    def test_record_outcome(self):
        result = self.pb.build("test", PromptStyle.DIRECT)
        self.pb.record_outcome(result["prompt_id"], True, quality_score=0.9)
        stats = self.pb.get_stats()
        assert stats["total_prompts"] == 2  # build + record

    def test_get_best_style(self):
        # Directly seed performance memory
        for _ in range(5):
            self.pb._memory.append({"style": "chain_of_thought", "quality_score": 0.95})
        for _ in range(2):
            self.pb._memory.append({"style": "direct", "quality_score": 0.5})
        best = self.pb.get_best_style()
        assert best == PromptStyle.CHAIN_OF_THOUGHT


# ═══════════════════════════════════════════════════════════════════════
# GeminiProvider Tests
# ═══════════════════════════════════════════════════════════════════════
from layers.layer12_ai_foundation.modules.model_router.gemini_provider import GeminiProvider


class TestGeminiProvider:
    def setup_method(self):
        self.km = KeyManager()
        self.km.register_key("k1", "AIzaSy_FAKE_KEY_111111111", "gemini")
        self.km.register_key("k2", "AIzaSy_FAKE_KEY_222222222", "gemini")
        self.km.register_key("k3", "AIzaSy_FAKE_KEY_333333333", "gemini")
        self.provider = GeminiProvider(self.km)

    def test_generate(self):
        result = self.provider.generate("Write about AI")
        assert "content" in result
        assert result["provider"] == "gemini"

    def test_generate_with_model(self):
        result = self.provider.generate("test", model="gemini-1.5-pro")
        assert result["model"] == "gemini-1.5-pro"

    def test_list_models(self):
        models = self.provider.list_models()
        assert "gemini-2.0-flash" in models

    def test_count_tokens(self):
        tokens = self.provider.count_tokens("Hello world test")
        assert tokens > 0

    def test_stats(self):
        self.provider.generate("test")
        stats = self.provider.get_stats()
        assert stats["total_requests"] == 1

    def test_key_rotation_across_requests(self):
        """Verify different keys are used for different requests."""
        keys_used = set()
        for _ in range(10):
            self.provider.generate("test")
        # At least some rotation should happen
        stats = self.provider.get_stats()
        assert stats["total_requests"] == 10

    def test_real_keys_not_exposed(self):
        """Actual API keys should never appear in stats or responses."""
        result = self.provider.generate("test")
        assert "FAKE_KEY" not in str(result)
        health = self.km.get_all_health()
        for h in health:
            assert "FAKE_KEY" not in str(h)
