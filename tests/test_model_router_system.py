"""System tests for the central model router."""

import pytest

from layers.layer12_ai_foundation.modules.model_router.model_router import (
    ModelResponse,
    ModelRouter,
    RequestType,
)


class TestModelRouter:
    def setup_method(self):
        self.router = ModelRouter()

    def test_generate_text(self):
        self.router.register_provider("gemini", handler=lambda r: "Generated text")
        response = self.router.generate_text("test")
        assert response.content == "Generated text"
        assert response.provider == "gemini"

    def test_generate_chat(self):
        self.router.register_provider("gemini", handler=lambda r: "Chat response")
        response = self.router.generate_chat([{"role": "user", "content": "Hello"}])
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
        assert response.content == ""
        assert response.provider == ""
        assert "no enabled provider with a handler" in response.metadata["error"]

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
