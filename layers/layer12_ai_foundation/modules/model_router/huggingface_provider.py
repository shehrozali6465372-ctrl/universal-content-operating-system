"""Hugging Face Inference Providers text adapter.

Uses the OpenAI-compatible router endpoint documented by Hugging Face.
The token is read only at request time from HF_TOKEN and is never persisted.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any, Dict, Optional


class HuggingFaceProvider:
    API_URL = "https://router.huggingface.co/v1/chat/completions"
    DEFAULT_MODEL = "openai/gpt-oss-120b:fastest"

    def __init__(self, token: Optional[str] = None, model: Optional[str] = None) -> None:
        self.token = str(token or os.getenv("HF_TOKEN") or "").strip()
        self.model = str(model or os.getenv("UCOS_HF_TEXT_MODEL") or self.DEFAULT_MODEL).strip()
        if not self.token:
            raise RuntimeError("HF_TOKEN is not configured")

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
        payload = {
            "model": model or self.model,
            "messages": messages,
            "stream": False,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 1024),
        }
        request = urllib.request.Request(
            self.API_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                body = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            try:
                detail = exc.read().decode("utf-8", "replace")
            except Exception:
                detail = ""
            raise RuntimeError(f"Hugging Face HTTP {exc.code}: {detail[:300]}") from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise RuntimeError(f"Hugging Face network error: {type(exc).__name__}") from exc
        except json.JSONDecodeError as exc:
            raise RuntimeError("Hugging Face returned invalid JSON") from exc

        choices = body.get("choices") or []
        if not choices:
            raise RuntimeError("Hugging Face returned no choices")
        message = choices[0].get("message") or {}
        content = str(message.get("content") or "").strip()
        if not content:
            raise RuntimeError("Hugging Face returned empty content")
        usage = body.get("usage") or {}
        return {
            "content": content,
            "text": content,
            "model": str(body.get("model") or payload["model"]),
            "provider": "huggingface_inference",
            "tokens_used": int(usage.get("total_tokens") or 0),
            "simulated": False,
        }
