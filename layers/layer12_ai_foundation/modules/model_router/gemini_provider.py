"""GeminiProvider — real Gemini API adapter using stdlib urllib.

Architecture:
    ModelRouter → GeminiProvider → KeyManager (key select) → Gemini API

    Real API call hota hai jab:
    1. KeyManager healthy key de
    2. GeminiProvider actual HTTP request bheje
    3. Response parse ho aur ModelResponse mein convert ho

    Agar network nahi hai to simulated response return hota hai.

Design Rules:
    - AI Brain ko kabhi pata nahi kaunsi key use ho rahi
    - KeyManager sirf credentials + health manage kare
    - PromptBuilder sirf prompts banaye, keys se alag
"""
from __future__ import annotations
import json
import os
import time
import urllib.request
import urllib.error
from typing import Any, Dict, List, Optional


class GeminiConfig:
    __slots__ = ("api_base", "default_model", "max_tokens",
                 "temperature", "timeout_seconds", "metadata")

    def __init__(self) -> None:
        self.api_base = "https://generativelanguage.googleapis.com/v1beta"
        self.default_model = "gemini-2.5-flash"
        self.max_tokens = 8192
        self.temperature = 0.7
        self.timeout_seconds = 60
        self.metadata: Dict[str, Any] = {}


class GeminiProvider:
    """Real Gemini API provider with intelligent key rotation.

    Supports:
    - Text generation (generateContent)
    - Chat (generateContent with history)
    - Image understanding (generateContent with image)
    - Streaming (streamGenerateContent)

    Falls back to simulated response when:
    - No network available
    - API key invalid
    - Rate limited on all keys
    """

    SUPPORTED_MODELS = [
        "gemini-2.5-flash", "gemini-2.5-pro", "gemini-3.5-flash", "gemini-3.6-flash", "gemini-3.1-flash-lite", "gemini-3-flash-preview", "gemini-2.0-flash", "gemini-2.0-flash-lite",
        "gemini-1.5-pro", "gemini-1.5-flash",
        "gemini-pro", "gemini-1.0-pro",
    ]

    def __init__(self, key_manager: Optional[Any] = None) -> None:
        self._key_manager = key_manager
        self._config = GeminiConfig()
        self._history: List[Dict[str, Any]] = []
        self._request_count = 0
        self._success_count = 0
        self._error_count = 0
        self._simulated_count = 0
        self._total_tokens = 0

    def add_key(self, key_id: str, actual_key: str) -> None:
        """Key register karo with KeyManager."""
        if self._key_manager:
            self._key_manager.register_key(key_id, actual_key, provider="gemini")

    def generate(self, prompt: str, model: str = "",
                 system_prompt: str = "", **kwargs: Any) -> Dict[str, Any]:
        """Text generate karo — real API call ya simulated."""
        start = time.time()
        model = model or self._config.default_model
        self._request_count += 1

        # Key select karo
        api_key = None
        key_id_used = None
        if self._key_manager:
            api_key = self._key_manager.select_key("text")
            if api_key:
                # Find which key_id was used
                for kid, khealth in self._key_manager._keys.items():
                    if khealth.is_available:
                        key_id_used = kid
                        break

        # Try real API call
        if api_key:
            result = self._real_api_call(prompt, model, api_key, system_prompt, **kwargs)
            if result is not None:
                latency = (time.time() - start) * 1000
                self._success_count += 1
                self._total_tokens += result.get("tokens_used", 0)

                # Report success
                if self._key_manager and key_id_used:
                    self._key_manager.report_success(
                        key_id_used, latency, result.get("tokens_used", 0))

                result["latency_ms"] = round(latency, 1)
                self._history.append({**result, "time": time.time()})
                return result
            else:
                # API call failed — report error
                self._error_count += 1
                if self._key_manager and key_id_used:
                    self._key_manager.report_error(key_id_used, "api_call_failed")

        # No simulated fallback — return error
        latency = (time.time() - start) * 1000
        error_result = {
            "text": "",
            "model": model,
            "provider": "gemini",
            "tokens_used": 0,
            "simulated": False,
            "error": "All API keys failed or unavailable",
            "latency_ms": round(latency, 1),
        }
        self._history.append({**error_result, "time": time.time()})
        return error_result

    def chat(self, messages: List[Dict[str, str]], model: str = "",
             **kwargs: Any) -> Dict[str, Any]:
        """Chat API — conversation history ke saath."""
        start = time.time()
        model = model or self._config.default_model
        self._request_count += 1

        api_key = None
        key_id_used = None
        if self._key_manager:
            api_key = self._key_manager.select_key("chat")
            if api_key:
                for kid, khealth in self._key_manager._keys.items():
                    if khealth.is_available:
                        key_id_used = kid
                        break

        if api_key:
            result = self._real_chat_call(messages, model, api_key, **kwargs)
            if result is not None:
                latency = (time.time() - start) * 1000
                self._success_count += 1
                result["latency_ms"] = round(latency, 1)
                if self._key_manager and key_id_used:
                    self._key_manager.report_success(key_id_used, latency, result.get("tokens_used", 0))
                self._history.append({**result, "time": time.time()})
                return result
            else:
                self._error_count += 1
                if self._key_manager and key_id_used:
                    self._key_manager.report_error(key_id_used, "chat_api_failed")

        # No simulated fallback — return error
        latency = (time.time() - start) * 1000
        error_result = {
            "text": "",
            "model": model,
            "provider": "gemini",
            "tokens_used": 0,
            "simulated": False,
            "error": "All API keys failed or unavailable",
            "latency_ms": round(latency, 1),
        }
        self._history.append({**error_result, "time": time.time()})
        return error_result

    def _real_api_call(self, prompt: str, model: str, api_key: str,
                       system_prompt: str = "",
                       **kwargs: Any) -> Optional[Dict[str, Any]]:
        """Actual Gemini REST API call using urllib."""
        url = f"{self._config.api_base}/models/{model}:generateContent?key={api_key}"

        contents = []
        if system_prompt:
            contents.append({
                "role": "user",
                "parts": [{"text": system_prompt}]
            })
            contents.append({
                "role": "model",
                "parts": [{"text": "Understood."}]
            })
        contents.append({
            "role": "user",
            "parts": [{"text": prompt}]
        })

        payload = {
            "contents": contents,
            "generationConfig": {
                "maxOutputTokens": kwargs.get("max_tokens", self._config.max_tokens),
                "temperature": kwargs.get("temperature", self._config.temperature),
            }
        }

        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                url, data=data,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=self._config.timeout_seconds) as resp:
                body = json.loads(resp.read().decode("utf-8"))

            # Parse Gemini response
            candidates = body.get("candidates", [])
            if not candidates:
                return None

            content_parts = candidates[0].get("content", {}).get("parts", [])
            text = "".join(part.get("text", "") for part in content_parts)

            usage = body.get("usageMetadata", {})
            tokens_used = usage.get("totalTokenCount", len(text.split()) * 2)

            return {
                "content": text,
                "model": model,
                "provider": "gemini",
                "tokens_used": tokens_used,
                "finish_reason": candidates[0].get("finishReason", "STOP"),
            }

        except urllib.error.HTTPError as exc:
            error_body = ""
            try:
                error_body = exc.read().decode("utf-8")
            except Exception:
                pass
            # Check if rate limited
            if exc.code == 429:
                if self._key_manager and self._key_manager._keys:
                    for kid in self._key_manager._keys:
                        self._key_manager.report_error(kid, "rate_limited_429", is_rate_limit=True)
            return None
        except (urllib.error.URLError, TimeoutError, OSError):
            return None
        except (json.JSONDecodeError, KeyError, IndexError):
            return None

    def _real_chat_call(self, messages: List[Dict[str, str]], model: str,
                        api_key: str, **kwargs: Any) -> Optional[Dict[str, Any]]:
        """Actual Gemini chat API call."""
        url = f"{self._config.api_base}/models/{model}:generateContent?key={api_key}"

        contents = []
        for msg in messages:
            role = msg.get("role", "user")
            gemini_role = "model" if role == "assistant" else "user"
            contents.append({
                "role": gemini_role,
                "parts": [{"text": msg.get("content", "")}]
            })

        payload = {
            "contents": contents,
            "generationConfig": {
                "maxOutputTokens": kwargs.get("max_tokens", self._config.max_tokens),
                "temperature": kwargs.get("temperature", self._config.temperature),
            }
        }

        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                url, data=data,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=self._config.timeout_seconds) as resp:
                body = json.loads(resp.read().decode("utf-8"))

            candidates = body.get("candidates", [])
            if not candidates:
                return None

            content_parts = candidates[0].get("content", {}).get("parts", [])
            text = "".join(part.get("text", "") for part in content_parts)
            usage = body.get("usageMetadata", {})

            return {
                "content": text,
                "model": model,
                "provider": "gemini",
                "tokens_used": usage.get("totalTokenCount", len(text.split()) * 2),
                "finish_reason": candidates[0].get("finishReason", "STOP"),
            }

        except Exception:
            return None

    def _simulated_response(self, prompt: str, model: str) -> Dict[str, Any]:
        """Simulated response — jab real API available nahi ho."""
        return {
            "content": (
                f"[SIMULATED/Gemini/{model}] "
                f"Response for: {prompt[:80]}... "
                f"(Set GEMINI_API_KEY env var for real responses)"
            ),
            "model": model,
            "provider": "gemini_simulated",
            "tokens_used": len(prompt.split()) * 2,
            "finish_reason": "SIMULATED",
            "simulated": True,
        }

    def count_tokens(self, text: str) -> int:
        """Approximate Gemini token count."""
        return len(text.split()) + len(text) // 4

    def list_models(self) -> List[str]:
        return self.SUPPORTED_MODELS

    def get_stats(self) -> Dict[str, Any]:
        return {
            "provider": "gemini",
            "total_requests": self._request_count,
            "successful_api_calls": self._success_count,
            "failed_api_calls": self._error_count,
            "simulated_responses": self._simulated_count,
            "total_tokens": self._total_tokens,
            "default_model": self._config.default_model,
            "models_supported": len(self.SUPPORTED_MODELS),
        }

    def get_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        return self._history[-limit:]
