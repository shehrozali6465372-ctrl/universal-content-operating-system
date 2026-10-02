"""DeepSeekProvider — real DeepSeek text/chat adapter behind ModelRouter."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional


class DeepSeekProvider:
    """DeepSeek API adapter using the canonical KeyManager credential boundary."""

    API_BASE = "https://api.deepseek.com"
    DEFAULT_MODEL = "deepseek-flash"
    SUPPORTED_MODELS = ("deepseek-flash", "deepseek-v4-pro")

    def __init__(self, key_manager: Any, timeout_seconds: int = 60) -> None:
        self._key_manager = key_manager
        self._timeout_seconds = timeout_seconds

    def generate(
        self,
        prompt: str,
        model: str = "",
        system_prompt: str = "",
        **kwargs: Any,
    ) -> Dict[str, Any]:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        return self._request(messages, model=model, **kwargs)

    def chat(
        self,
        messages: List[Dict[str, str]],
        model: str = "",
        **kwargs: Any,
    ) -> Dict[str, Any]:
        return self._request(messages, model=model, **kwargs)

    def _request(
        self,
        messages: List[Dict[str, str]],
        model: str = "",
        **kwargs: Any,
    ) -> Dict[str, Any]:
        selected = self._key_manager.select_key_with_id("text", provider="deepseek")
        if not selected:
            return {"content": "", "provider": "deepseek", "error": "No healthy DeepSeek credential configured"}

        key_id, api_key = selected
        model = model or self.DEFAULT_MODEL
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": int(kwargs.get("max_tokens", 8192)),
            "stream": False,
        }
        if "temperature" in kwargs:
            payload["temperature"] = kwargs["temperature"]

        started = time.time()
        request = urllib.request.Request(
            f"{self.API_BASE}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self._timeout_seconds) as response:
                body = json.loads(response.read().decode("utf-8"))
            content = str(((body.get("choices") or [{}])[0].get("message") or {}).get("content") or "").strip()
            if not content:
                raise RuntimeError("DeepSeek returned empty content")
            usage = body.get("usage") or {}
            tokens = int(usage.get("total_tokens") or 0)
            latency = (time.time() - started) * 1000
            self._key_manager.report_success(key_id, latency, tokens)
            return {
                "content": content,
                "provider": "deepseek",
                "model": str(body.get("model") or model),
                "tokens_used": tokens,
            }
        except urllib.error.HTTPError as exc:
            self._key_manager.report_error(key_id, f"DeepSeek HTTP {exc.code}", is_rate_limit=exc.code == 429)
            return {"content": "", "provider": "deepseek", "model": model, "error": f"DeepSeek HTTP {exc.code}"}
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            self._key_manager.report_error(key_id, f"DeepSeek network error: {type(exc).__name__}")
            return {"content": "", "provider": "deepseek", "model": model, "error": f"DeepSeek network error: {type(exc).__name__}"}
        except (json.JSONDecodeError, KeyError, IndexError, TypeError, ValueError) as exc:
            self._key_manager.report_error(key_id, f"DeepSeek response parse error: {type(exc).__name__}")
            return {"content": "", "provider": "deepseek", "model": model, "error": f"DeepSeek response parse error: {type(exc).__name__}"}
