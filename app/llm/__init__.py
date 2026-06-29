"""LLM provider factory.

The whole platform depends only on the `LLMProvider` interface — never on a
specific vendor. Choosing a provider is config + an API key, nothing more.
"""
from __future__ import annotations

import os

from .base import LLMProvider
from .stub import StubProvider


def get_llm() -> LLMProvider:
    provider = os.environ.get("LLM_PROVIDER", "auto").lower()

    if provider in ("auto", "gemini") and os.environ.get("GEMINI_API_KEY"):
        try:
            from .gemini import GeminiProvider
            return GeminiProvider()
        except Exception as exc:  # pragma: no cover - depends on env
            print(f"[llm] Gemini unavailable ({exc}); falling back to offline stub.")

    return StubProvider()
