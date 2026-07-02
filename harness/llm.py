"""Minimal chat clients for Anthropic and OpenRouter.

API keys come from .env / environment (ANTHROPIC_API_KEY, OPENROUTER_API_KEY);
they are never logged.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass

import httpx
from dotenv import load_dotenv

_RETRIES = 3
_RETRY_STATUS = {429, 500, 502, 503, 529}


class LLMError(RuntimeError):
    pass


@dataclass
class LLMReply:
    text: str
    input_tokens: int
    output_tokens: int


def _post_with_retries(url: str, headers: dict, payload: dict) -> dict:
    last_error: Exception | None = None
    for attempt in range(_RETRIES):
        try:
            resp = httpx.post(url, headers=headers, json=payload, timeout=300.0)
            if resp.status_code in _RETRY_STATUS:
                last_error = LLMError(f"HTTP {resp.status_code}: {resp.text[:500]}")
            elif resp.status_code != 200:
                raise LLMError(f"HTTP {resp.status_code}: {resp.text[:500]}")
            else:
                return resp.json()
        except httpx.HTTPError as exc:
            last_error = exc
        time.sleep(2**attempt)
    raise LLMError(f"request failed after {_RETRIES} attempts: {last_error}")


def _require_key(name: str) -> str:
    load_dotenv()
    key = os.environ.get(name)
    if not key:
        raise LLMError(f"{name} not set (expected in environment or .env)")
    return key


class AnthropicClient:
    URL = "https://api.anthropic.com/v1/messages"

    def __init__(self, model: str, temperature: float = 1.0, max_tokens: int = 4096):
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._key = _require_key("ANTHROPIC_API_KEY")

    def chat(self, system: str, messages: list[dict]) -> LLMReply:
        data = _post_with_retries(
            self.URL,
            headers={
                "x-api-key": self._key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            payload={
                "model": self.model,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "system": system,
                "messages": messages,
            },
        )
        text = "".join(b.get("text", "") for b in data["content"] if b.get("type") == "text")
        usage = data.get("usage", {})
        return LLMReply(text, usage.get("input_tokens", 0), usage.get("output_tokens", 0))


class OpenRouterClient:
    URL = "https://openrouter.ai/api/v1/chat/completions"

    def __init__(self, model: str, temperature: float = 1.0, max_tokens: int = 4096):
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._key = _require_key("OPENROUTER_API_KEY")

    def chat(self, system: str, messages: list[dict]) -> LLMReply:
        data = _post_with_retries(
            self.URL,
            headers={
                "Authorization": f"Bearer {self._key}",
                "content-type": "application/json",
            },
            payload={
                "model": self.model,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "messages": [{"role": "system", "content": system}, *messages],
            },
        )
        text = data["choices"][0]["message"]["content"] or ""
        usage = data.get("usage", {})
        return LLMReply(text, usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0))


def make_client(model: str, temperature: float = 1.0, max_tokens: int = 4096):
    """Anthropic for claude-* model names, OpenRouter for everything else."""
    if model.startswith("claude"):
        return AnthropicClient(model, temperature, max_tokens)
    return OpenRouterClient(model, temperature, max_tokens)
