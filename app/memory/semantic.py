from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from ..models import Evidence, Feedback, Interaction
from .base import Memory
from .embeddings import EmbeddingProvider, get_embedder
from .graph import KnowledgeGraph
from .store import Store
from .vectorstore import VectorStore


class SemanticMemory(Memory):
    def __init__(
        self,
        store: Store,
        embedder: Optional[EmbeddingProvider] = None,
        playbooks_path: Optional[str | Path] = None,
    ) -> None:
        self.store = store
        self.embed = embedder or get_embedder()
        self.vec = VectorStore(self.embed.dim)        
        self.dec = VectorStore(self.embed.dim)        
        self.graph = KnowledgeGraph()
        self._org: list[dict] = []

        if playbooks_path:
            self._org = json.loads(Path(playbooks_path).read_text(encoding="utf-8"))
            for doc in self._org:
                self.vec.add(
                    doc["id"],
                    self.embed.embed(f"{doc['title']} {doc['body']}"),
                    {"scope": "org", "ref": doc["id"], "source": "org_knowledge",
                     "snippet": _clip(doc["body"]), "title": doc["title"]},
                )
                self.graph.add_playbook(doc)

        
        for acc in self.store.all_accounts():
            self.graph.add_account(acc["id"], acc.get("name", ""))
        for it in self.store.all_interactions():
            self._index(it)
        for d in self.store.decisions():
            self._index_decision(d["account_id"], d["action"], d["decision"], d.get("context", ""))

    # ---- Memory lifecycle ----
    def remember(self, item: Interaction) -> None:
        self.store.add_interaction(item)
        self._index(item)

    def recall(self, query: str, account_id: Optional[str] = None, k: int = 6) -> list[Evidence]:
        qv = self.embed.embed(query)

        def where(m: dict) -> bool:
            return m.get("scope") == "org" or (account_id is not None and m.get("account_id") == account_id)

        hits = self.vec.search(qv, k=k + 4, where=where)

        # graph expansion: pull playbooks that ADDRESS this account's live entities
        expanded: list[tuple[float, dict]] = []
        if account_id:
            entities = self.graph.entities_for_account(account_id)
            have = {h[1].get("ref") for h in hits}
            for pb in self.graph.playbooks_for(entities):
                doc_id = pb.split(":", 1)[1]
                doc = next((d for d in self._org if d["id"] == doc_id), None)
                if doc and doc_id not in have:
                    expanded.append(
                        (0.34, {"scope": "org", "ref": doc_id, "source": "org_knowledge",
                                "snippet": _clip(doc["body"]), "title": doc["title"]})
                    )

        evidence = [
            Evidence(source=m["source"], ref=m["ref"], snippet=m["snippet"], score=round(float(s), 3))
            for s, m in (hits + expanded)
        ]
        seen: set[str] = set()
        deduped: list[Evidence] = []
        for ev in sorted(evidence, key=lambda e: -e.score):
            if ev.ref not in seen:
                seen.add(ev.ref)
                deduped.append(ev)
        return deduped[:k]

    def improve(self, feedback: Feedback) -> None:
        context = self._account_snapshot(feedback.account_id)
        self.store.add_decision(feedback, context)
        self._index_decision(feedback.account_id, feedback.action, feedback.decision, context)
        self.graph.add_decision(feedback.account_id, feedback.action, feedback.decision)

    def forget(self, ref: str) -> None:
        self.store.delete_interaction(ref)
        self.vec.delete(ref)
        if f"interaction:{ref}" in self.graph.g:
            self.graph.g.remove_node(f"interaction:{ref}")

    
    def interactions(self, account_id: str) -> list[Interaction]:
        return self.store.interactions(account_id)

    def rejected_actions(self, account_id: str) -> list[str]:
        return [d["action"] for d in self.store.decisions(account_id) if d["decision"] == "rejected"]

    # ---- extended capabilities (override Memory defaults) ----
    def recall_decisions(self, query: str, k: int = 3) -> list[dict]:
        return [
            {"action": m["action"], "decision": m["decision"], "account_id": m["account_id"], "score": round(s, 3)}
            for s, m in self.dec.search(self.embed.embed(query), k=k)
        ]

    def graph_export(self, account_id: Optional[str] = None) -> dict:
        return self.graph.export(account_id)

    
    def _index(self, it: Interaction) -> None:
        self.vec.add(
            it.id,
            self.embed.embed(it.text),
            {"scope": "account", "account_id": it.account_id, "ref": it.id,
             "source": "account_history", "snippet": _clip(it.text), "kind": it.kind},
        )
        self.graph.add_interaction(it)

    def _index_decision(self, account_id: str, action: str, decision: str, context: str) -> None:
        self.dec.add(
            f"{account_id}:{action}",
            self.embed.embed(f"{action} {context}"),
            {"account_id": account_id, "action": action, "decision": decision},
        )

    def _account_snapshot(self, account_id: str) -> str:
        return " ".join(i.text for i in self.store.interactions(account_id))[:1000]


def _clip(text: str, n: int = 200) -> str:
    return text if len(text) <= n else text[:n] + "…"
