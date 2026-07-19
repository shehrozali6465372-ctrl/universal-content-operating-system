"""ModelRouter — AI Brain ko abstract kare keys se.

Architecture:
    AI Brain
        │
        ▼
    ModelRouter        ← AI Brain sirf "text generate" ya "image generate" bole
        │
        ├── TextRouter → Any Healthy Key
        ├── ImageRouter → Any Healthy Key
        └── EmbeddingRouter → Any Healthy Key
        │
        ▼
    KeyManager         ← Sirf auth, health, rate limits
        │
        ▼
    Provider API

Design Rules:
    1. AI Brain ko kabhi pata nahi kaunsi key use ho rahi hai
    2. Keys sirf credentials hain, routing logic router ki hai
    3. Kal OpenAI/Claude/DeepSeek add karo — AI Brain mein koi change nahi
    4. PromptBuilder aur KeyManager kabhi mix nahi honge
"""
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
    """AI Brain ka request — keys ka koi mention nahi."""
    __slots__ = ("request_id", "request_type", "prompt", "model", "parameters",
                 "system_prompt", "metadata")

    def __init__(self, request_type: RequestType, prompt: str,
                 model: str = "", **kwargs: Any) -> None:
        self.request_id = str(uuid.uuid4())[:12]
        self.request_type = request_type
        self.prompt = prompt
        self.model = model
        self.parameters: Dict[str, Any] = kwargs
        self.system_prompt = kwargs.pop("system_prompt", "")
        self.metadata: Dict[str, Any] = {}


class ModelResponse:
    """Provider ka response — router format kare."""
    __slots__ = ("request_id", "content", "provider", "model_used",
                 "tokens_used", "latency_ms", "metadata")

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
    """Kal naya provider add karna ho — sirf yeh adapter banaye."""

    __slots__ = ("provider_name", "capabilities", "is_enabled", "handler",
                 "config", "metadata")

    def __init__(self, provider_name: str, handler: Optional[Callable] = None,
                 capabilities: Optional[List[RequestType]] = None) -> None:
        self.provider_name = provider_name
        self.handler = handler
        self.capabilities = capabilities or [RequestType.TEXT, RequestType.CHAT]
        self.is_enabled = True
        self.config: Dict[str, Any] = {}
        self.metadata: Dict[str, Any] = {}

    def supports(self, request_type: RequestType) -> bool:
        return request_type in self.capabilities

    def to_dict(self) -> Dict[str, Any]:
        return {
            "provider": self.provider_name,
            "enabled": self.is_enabled,
            "capabilities": [c.value for c in self.capabilities],
        }


class ModelRouter:
    """AI Brain ka single entry point.

    AI Brain bole: "text generate karo" ya "image generate karo"
    Router decide kare: kaunsa provider, kaunsi key, kaunsa model
    """

    def __init__(self, key_manager: Any = None) -> None:
        self._key_manager = key_manager
        self._providers: Dict[str, ProviderAdapter] = {}
        self._routing_table: Dict[RequestType, List[str]] = {}
        self._history: List[Dict[str, Any]] = []
        self._fallback_enabled = True
        self._max_retries = 3

    def register_provider(self, provider_name: str,
                          handler: Optional[Callable] = None,
                          capabilities: Optional[List[RequestType]] = None) -> ProviderAdapter:
        adapter = ProviderAdapter(provider_name, handler, capabilities)
        self._providers[provider_name] = adapter
        return adapter

    def unregister_provider(self, provider_name: str) -> bool:
        if provider_name in self._providers:
            del self._providers[provider_name]
            for rtype in self._routing_table:
                self._routing_table[rtype] = [
                    p for p in self._routing_table[rtype] if p != provider_name
                ]
            return True
        return False

    def set_routing(self, request_type: RequestType,
                    provider_order: List[str]) -> None:
        """Routing priority set karo."""
        self._routing_table[request_type] = provider_order

    def _select_provider(self, request_type: RequestType) -> Optional[ProviderAdapter]:
        """Best provider select karo for this request type."""
        # Pehle routing table check karo
        order = self._routing_table.get(request_type, [])
        for provider_name in order:
            adapter = self._providers.get(provider_name)
            if adapter and adapter.is_enabled and adapter.supports(request_type):
                return adapter

        # Routing table mein nahi to capability se dhundo
        for adapter in self._providers.values():
            if adapter.is_enabled and adapter.supports(request_type):
                return adapter

        return None

    def route(self, request: ModelRequest) -> ModelResponse:
        """AI Brain ka request route karo.

        AI Brain ko sirf ModelResponse milegi.
        Keys, providers, routing — sab internal hai.
        """
        response = ModelResponse(request.request_id)
        start = time.time()

        # Try primary provider
        adapter = self._select_provider(request.request_type)
        if adapter and adapter.handler:
            try:
                result = adapter.handler(request)
                if isinstance(result, ModelResponse):
                    response = result
                elif isinstance(result, str):
                    response.content = result
                response.provider = adapter.provider_name
                response.model_used = request.model or adapter.provider_name
                response.latency_ms = (time.time() - start) * 1000
                self._history.append({
                    "request_id": request.request_id,
                    "type": request.request_type.value,
                    "provider": adapter.provider_name,
                    "status": "success",
                    "latency_ms": response.latency_ms,
                    "time": time.time(),
                })
                return response
            except Exception as exc:
                # Fallback enabled hai to try next provider
                if not self._fallback_enabled:
                    response.content = f"Error: {exc}"
                    return response

        # Fallback — try all other providers
        if self._fallback_enabled:
            for padapter in self._providers.values():
                if padapter.is_enabled and padapter.supports(request.request_type):
                    try:
                        if padapter.handler:
                            result = padapter.handler(request)
                            if isinstance(result, ModelResponse):
                                response = result
                            elif isinstance(result, str):
                                response.content = result
                            response.provider = padapter.provider_name
                            response.latency_ms = (time.time() - start) * 1000
                            return response
                    except Exception:
                        continue

        response.content = "No available provider for this request type"
        response.latency_ms = (time.time() - start) * 1000
        return response

    def generate_text(self, prompt: str, model: str = "",
                      **kwargs: Any) -> ModelResponse:
        """Convenience method — AI Brain ka main interface."""
        request = ModelRequest(RequestType.TEXT, prompt, model, **kwargs)
        return self.route(request)

    def generate_chat(self, messages: List[Dict[str, str]], model: str = "",
                      **kwargs: Any) -> ModelResponse:
        request = ModelRequest(RequestType.CHAT, str(messages), model, **kwargs)
        return self.route(request)

    def generate_image(self, prompt: str, model: str = "",
                       **kwargs: Any) -> ModelResponse:
        request = ModelRequest(RequestType.IMAGE, prompt, model, **kwargs)
        return self.route(request)

    def generate_embedding(self, text: str, model: str = "",
                           **kwargs: Any) -> ModelResponse:
        request = ModelRequest(RequestType.EMBEDDING, text, model, **kwargs)
        return self.route(request)

    def list_providers(self) -> List[Dict[str, Any]]:
        return [p.to_dict() for p in self._providers.values()]

    def get_stats(self) -> Dict[str, Any]:
        total = len(self._history)
        success = sum(1 for h in self._history if h["status"] == "success")
        providers_used = set(h["provider"] for h in self._history)
        return {
            "total_requests": total,
            "success": success,
            "failed": total - success,
            "success_rate": round(success / max(total, 1) * 100, 1),
            "providers_used": list(providers_used),
            "providers_registered": len(self._providers),
        }

    def get_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        return self._history[-limit:]
