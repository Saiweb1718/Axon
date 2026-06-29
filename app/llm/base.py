"""The single LLM seam every agent and the planner depend on."""
from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from typing import Any


class LLMProvider(ABC):
    name: str = "base"

    @abstractmethod
    def complete(self, system: str, prompt: str) -> str:
        ...

    def complete_json(self, system: str, prompt: str) -> dict[str, Any]:
        """Convenience wrapper: ask for JSON and parse it defensively."""
        raw = self.complete(system, prompt)
        return extract_json(raw)


def extract_json(text: str) -> dict[str, Any]:
    text = (text or "").strip()
    # strip ```json fences if a model added them
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*", "", text).rstrip("`").strip()
    match = re.search(r"\{.*\}", text, re.S)
    if match:
        text = match.group(0)
    try:
        return json.loads(text)
    except Exception:
        return {}
