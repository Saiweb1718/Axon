from __future__ import annotations

import os
import time
from typing import Any

from .base import LLMProvider, extract_json
from .stub import StubProvider


class GeminiProvider(LLMProvider):
    name = "gemini"

    def __init__(self, model: str | None = None, max_retries: int = 2) -> None:
        from google import genai  # lazy: the stub path needs no dep
        from google.genai import types

        key = os.environ.get("GEMINI_API_KEY")
        if not key:
            raise RuntimeError("GEMINI_API_KEY not set")
        self._types = types
        self._client = genai.Client(api_key=key, http_options=types.HttpOptions(timeout=20_000))
        self._model_name = model or os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
        self.name = f"gemini:{self._model_name}"
        self._max_retries = max_retries
        self._fallback = StubProvider()  # keep the demo alive on a network blip

    def _generate(self, system: str, prompt: str, json_mode: bool) -> str:
        cfg: dict[str, Any] = {
            "temperature": 0.2,
            # Disable "thinking": these are short, structured tasks — thinking just adds
            # seconds of latency and burns tokens/quota. Big speed-up on gemini-2.5-flash.
            "thinking_config": self._types.ThinkingConfig(thinking_budget=0),
        }
        if json_mode:
            cfg["response_mime_type"] = "application/json"
        resp = self._client.models.generate_content(
            model=self._model_name,
            contents=f"{system}\n\n{prompt}",
            config=self._types.GenerateContentConfig(**cfg),
        )
        return getattr(resp, "text", "") or ""

    def _call(self, system: str, prompt: str, json_mode: bool) -> str:
        last: Exception | None = None
        for attempt in range(self._max_retries):
            try:
                text = self._generate(system, prompt, json_mode)
                if text.strip():
                    return text
            except Exception as exc:  # transient API/network error
                last = exc
                if _is_quota_error(exc):
                    break  # daily/per-minute quota won't recover in-loop — fall back now
            time.sleep(0.5 * (attempt + 1))  # gentle backoff for transient errors
        reason = "quota exhausted" if _is_quota_error(last) else f"{self._max_retries} retries failed"
        print(f"[gemini] {reason} ({type(last).__name__}); using offline stub for this call.")
        return self._fallback.complete(system, prompt)

    def complete(self, system: str, prompt: str) -> str:
        return self._call(system, prompt, json_mode=False)

    def complete_json(self, system: str, prompt: str) -> dict[str, Any]:
        return extract_json(self._call(system, prompt, json_mode=True))


def _is_quota_error(exc: Exception | None) -> bool:
    m = str(exc).lower()
    return "429" in m or "resource_exhausted" in m or "quota" in m
