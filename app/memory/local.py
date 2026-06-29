from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from ..models import Evidence, Feedback, Interaction
from .base import Memory


class LocalMemory(Memory):
    def __init__(self, playbooks_path: Optional[str | Path] = None) -> None:
        self._interactions: dict[str, list[Interaction]] = {}
        self._org: list[dict] = []                  
        self._rejected: dict[str, list[str]] = {}  
        if playbooks_path:
            self._org = json.loads(Path(playbooks_path).read_text(encoding="utf-8"))

    
    def remember(self, item: Interaction) -> None:
        self._interactions.setdefault(item.account_id, []).append(item)

    def recall(self, query: str, account_id: Optional[str] = None, k: int = 6) -> list[Evidence]:
        terms = set(_tokens(query))
        scored: list[tuple[int, Evidence]] = []

        if account_id:
            for it in self._interactions.get(account_id, []):
                s = _overlap(terms, it.text)
                if s:
                    scored.append((s, Evidence(source="account_history", ref=it.id, snippet=_clip(it.text))))

        for doc in self._org:
            s = _overlap(terms, f"{doc['title']} {doc['body']}")
            if s:
                scored.append((s, Evidence(source="org_knowledge", ref=doc["id"], snippet=_clip(doc["body"]))))

        scored.sort(key=lambda x: -x[0])
        return [ev for _, ev in scored[:k]]

    def improve(self, feedback: Feedback) -> None:
        if feedback.decision == "rejected":
            self._rejected.setdefault(feedback.account_id, []).append(feedback.action)

    def forget(self, ref: str) -> None:
        for acc in list(self._interactions):
            self._interactions[acc] = [i for i in self._interactions[acc] if i.id != ref]
        self._org = [d for d in self._org if d["id"] != ref]

    
    def interactions(self, account_id: str) -> list[Interaction]:
        return self._interactions.get(account_id, [])

    def rejected_actions(self, account_id: str) -> list[str]:
        return self._rejected.get(account_id, [])


def _tokens(text: str) -> list[str]:
    cleaned = "".join(c.lower() if c.isalnum() else " " for c in text)
    return [w for w in cleaned.split() if len(w) > 2]


def _overlap(terms: set[str], text: str) -> int:
    return len(terms & set(_tokens(text)))


def _clip(text: str, n: int = 200) -> str:
    return text if len(text) <= n else text[:n] + "…"
