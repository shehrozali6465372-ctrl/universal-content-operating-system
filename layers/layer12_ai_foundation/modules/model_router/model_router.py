"""ModelRouter — central provider routing with explicit failure semantics."""
from __future__ import annotations
import time
import uuid
from typing import Any, Callable, Dict, List, Optional
from enum import Enum


class RequestType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    EMBEDDING = "embedding"
    CHAT = "chat"
    TRANSCRIPTION = "transcription"


class ModelProvider(str, Enum):
    GEMINI = "gemini"
    OPENAI = "openai"
    CLAUDE = "claude"
    DEEPSEEK = "deepseek"
    GROK = "grok"
    OLLAMA = "ollama"
    LOCAL = "local"


class ModelRequest:
    __slots__ = ("request_id", "request_type", "prompt", "model", "parameters", "system_prompt", "metadata")

    def __init__(self, request_type: RequestType, prompt: str, model: str = "", **kwargs: Any) -> None:
        self.request_id = str(uuid.uuid4())[:12]
        self.request_type = request_type
        self.prompt = prompt
        self.model = model
        self.parameters: Dict[str, Any] = kwargs
        self.system_prompt = kwargs.pop("system_prompt", "")
        self.metadata: Dict[str, Any] = {}


class ModelResponse:
    __slots__ = ("request_id", "content", "provider", "model_used", "tokens_used", "latency_ms", "metadata")

    def __init__(self, request_id: str, content: str = "") -> None:
        self.request_id = request_id
        self.content = content
        self.provider = ""
        self.model_used = ""
        self.tokens_used = 0
        self.latency_ms = 0.0
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "content": self.content[:500],
            "provider": self.provider,
            "model_used": self.model_used,
            "tokens_used": self.tokens_used,
            "latency_ms": round(self.latency_ms, 1),
        }


class ProviderAdapter:
    __slots__ = ("provider_name", "capabilities", "is_enabled", "handler", "config", "metadata")

    def __init__(self, provider_name: str, handler: Optional[Callable] = None, capabilities: Optional[List[RequestType]] = None) -> None:
        self.provider_name = provider_name
        self.handler = handler
        self.capabilities = capabilities or [RequestType.TEXT, RequestType.CHAT]
        self.is_enabled = True
        self.config: Dict[str, Any] = {}
        self.metadata: Dict[str, Any] = {}

    def supports(self, request_type: RequestType) -> bool:
        return request_type in self.capabilities

    def to_dict(self) -> Dict[str, Any]:
        return {"provider": self.provider_name, "enabled": self.is_enabled, "capabilities": [c.value for c in self.capabilities]}


class ModelRouter:
    """Single AI entry point; providers and credentials remain behind the router."""

    def __init__(self, key_manager: Any = None) -> None:
        self._key_manager = key_manager
        self._providers: Dict[str, ProviderAdapter] = {}
        self._routing_table: Dict[RequestType, List[str]] = {}
        self._history: List[Dict[str, Any]] = []
        self._fallback_enabled = True
        self._max_retries = 3
        self._max_history = 1000

    def register_provider(self, provider_name: str, handler: Optional[Callable] = None, capabilities: Optional[List[RequestType]] = None) -> ProviderAdapter:
        adapter = ProviderAdapter(provider_name, handler, capabilities)
        self._providers[provider_name] = adapter
        return adapter

    def unregister_provider(self, provider_name: str) -> bool:
        if provider_name in self._providers:
            del self._providers[provider_name]
            for rtype in self._routing_table:
                self._routing_table[rtype] = [p for p in self._routing_table[rtype] if p != provider_name]
            return True
        return False

    def set_routing(self, request_type: RequestType, provider_order: List[str]) -> None:
        self._routing_table[request_type] = provider_order

    def _provider_order(self, request_type: RequestType) -> List[ProviderAdapter]:
        """Return configured routing order, then unlisted providers."""
        ordered: List[ProviderAdapter] = []
        seen: set[str] = set()
        for provider_name in self._routing_table.get(request_type, []):
            adapter = self._providers.get(provider_name)
            if adapter and provider_name not in seen:
                ordered.append(adapter)
                seen.add(provider_name)
        for provider_name, adapter in self._providers.items():
            if provider_name not in seen:
                ordered.append(adapter)
                seen.add(provider_name)
        return ordered

    def _select_provider(self, request_type: RequestType) -> Optional[ProviderAdapter]:
        for adapter in self._provider_order(request_type):
            if adapter.is_enabled and adapter.supports(request_type) and adapter.handler:
                return adapter
        return None

    def _record(self, request: ModelRequest, provider: str, status: str, latency_ms: float, error: str = "") -> None:
        self._history.append({
            "request_id": request.request_id,
            "type": request.request_type.value,
            "provider": provider,
            "status": status,
            "latency_ms": latency_ms,
            "time": time.time(),
            **({"error": error} if error else {}),
        })
        if len(self._history) > self._max_history:
            del self._history[:-self._max_history]

    @staticmethod
    def _apply_result(response: ModelResponse, result: Any, adapter: ProviderAdapter, request: ModelRequest) -> ModelResponse:
        if isinstance(result, ModelResponse):
            response = result
        elif isinstance(result, str):
            response.content = result
        elif isinstance(result, dict):
            response.content = result.get("content", result.get("text", ""))
            response.model_used = result.get("model", "")
            response.tokens_used = result.get("tokens_used", 0) or 0
            response.metadata.update(result.get("metadata", {}) or {})
            if result.get("error"):
                raise RuntimeError(str(result["error"]))
        else:
            raise RuntimeError("provider returned unsupported response type")
        if not (response.content or "").strip():
            raise RuntimeError("provider returned empty content")
        response.provider = response.provider or adapter.provider_name
        response.model_used = response.model_used or request.model or adapter.provider_name
        return response

    def route(self, request: ModelRequest) -> ModelResponse:
        start = time.time()
        attempted: set[str] = set()
        failures: List[str] = []
        providers = [
            adapter for adapter in self._provider_order(request.request_type)
            if adapter.is_enabled
            and adapter.supports(request.request_type)
            and adapter.handler
        ]
        if not self._fallback_enabled:
            providers = providers[:1]

        for adapter in providers:
            attempted.add(adapter.provider_name)
            try:
                response = self._apply_result(
                    ModelResponse(request.request_id),
                    adapter.handler(request),
                    adapter,
                    request,
                )
                response.latency_ms = (time.time() - start) * 1000
                self._record(request, adapter.provider_name, "success", response.latency_ms)
                return response
            except Exception as exc:
                failures.append(f"{adapter.provider_name}: {exc}")
                self._record(
                    request, adapter.provider_name, "failed",
                    (time.time() - start) * 1000, str(exc)
                )

        detail = "; ".join(failures) if failures else "no enabled provider with a handler"
        response = ModelResponse(request.request_id)
        response.provider = ""
        response.latency_ms = (time.time() - start) * 1000
        response.metadata["error"] = detail
        self._record(request, "", "failed", response.latency_ms, detail)
        return response

    def generate_text(self, prompt: str, model: str = "", **kwargs: Any) -> ModelResponse:
        return self.route(ModelRequest(RequestType.TEXT, prompt, model, **kwargs))

    def generate_chat(self, messages: List[Dict[str, str]], model: str = "", **kwargs: Any) -> ModelResponse:
        # Preserve message structure for chat-capable provider handlers.
        request = ModelRequest(RequestType.CHAT, "", model, **kwargs)
        request.metadata["messages"] = messages
        request.parameters["messages"] = messages
        return self.route(request)

    def generate_image(self, prompt: str, model: str = "", **kwargs: Any) -> ModelResponse:
        return self.route(ModelRequest(RequestType.IMAGE, prompt, model, **kwargs))

    def generate_embedding(self, text: str, model: str = "", **kwargs: Any) -> ModelResponse:
        return self.route(ModelRequest(RequestType.EMBEDDING, text, model, **kwargs))

    def list_providers(self) -> List[Dict[str, Any]]:
        return [p.to_dict() for p in self._providers.values()]

    def get_stats(self) -> Dict[str, Any]:
        total = len(self._history)
        success = sum(1 for h in self._history if h["status"] == "success")
        providers_used = set(h["provider"] for h in self._history if h["provider"])
        return {"total_requests": total, "success": success, "failed": total - success, "success_rate": round(success / max(total, 1) * 100, 1), "providers_used": list(providers_used), "providers_registered": len(self._providers)}

    def get_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        return self._history[-max(1, min(limit, self._max_history)):]
