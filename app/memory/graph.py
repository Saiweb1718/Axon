from __future__ import annotations

import re

import networkx as nx

from ..models import Interaction

# typed lexicons -> entity nodes (entity = "<type>:<term>")
LEXICON: dict[str, list[str]] = {
    "risk": [
        "churn", "cancel", "downgrade", "unhappy", "frustrat", "roi", "value",
        "budget", "cost", "competitor", "escalat", "decline", "drop", "risk", "concern", "confusion",
    ],
    "opportunity": [
        "expansion", "expand", "upgrade", "upsell", "seat", "seats", "add users",
        "interested", "growth", "scale", "more access", "licens", "sub-team", "volume pricing",
    ],
    "stakeholder": [
        "cfo", "ceo", "cto", "champion", "admin", "procurement", "executive",
        "exec", "sponsor", "economic buyer", "finance",
    ],
    "product": [
        "usage", "login", "adoption", "api", "integration", "feature",
        "onboarding", "training", "dashboard", "report", "workflow", "active users",
    ],
}


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9 ]", " ", s.lower())


class KnowledgeGraph:
    def __init__(self) -> None:
        self.g = nx.DiGraph()

    
    def add_account(self, account_id: str, name: str = "") -> None:
        self.g.add_node(f"account:{account_id}", type="account", label=name or account_id)

    def add_playbook(self, doc: dict) -> None:
        nid = f"playbook:{doc['id']}"
        self.g.add_node(nid, type="playbook", label=doc.get("title", doc["id"]))
        for etype, ent in self._extract(f"{doc.get('title', '')} {doc.get('body', '')}"):
            self.g.add_node(ent, type=etype, label=ent.split(":", 1)[1])
            self.g.add_edge(nid, ent, rel="addresses")

    def add_interaction(self, it: Interaction) -> None:
        acc = f"account:{it.account_id}"
        if acc not in self.g:
            self.add_account(it.account_id)
        nid = f"interaction:{it.id}"
        self.g.add_node(nid, type="interaction", label=it.kind, text=it.text, ts=it.ts)
        self.g.add_edge(acc, nid, rel="has_signal")
        for etype, ent in self._extract(it.text):
            self.g.add_node(ent, type=etype, label=ent.split(":", 1)[1])
            self.g.add_edge(nid, ent, rel="mentions")
            self.g.add_edge(acc, ent, rel="associated_with")

    def add_decision(self, account_id: str, action: str, decision: str) -> None:
        acc = f"account:{account_id}"
        if acc not in self.g:
            self.add_account(account_id)
        nid = f"decision:{_norm(action)[:36].strip()}|{account_id}"
        self.g.add_node(nid, type="decision", label=f"{decision}: {action[:54]}", decision=decision)
        self.g.add_edge(acc, nid, rel="decided")

    
    def entities_for_account(self, account_id: str) -> list[str]:
        acc = f"account:{account_id}"
        if acc not in self.g:
            return []
        return [
            n for n in self.g.successors(acc)
            if self.g.nodes[n].get("type") in ("risk", "opportunity", "stakeholder", "product")
        ]

    def playbooks_for(self, entities: list[str]) -> list[str]:
        out: list[str] = []
        for ent in entities:
            if ent not in self.g:
                continue
            for pred in self.g.predecessors(ent):
                if self.g.nodes[pred].get("type") == "playbook":
                    out.append(pred)
        return list(dict.fromkeys(out))

    def export(self, account_id: str | None = None) -> dict:
        if account_id:
            acc = f"account:{account_id}"
            if acc not in self.g:
                return {"nodes": [], "edges": []}
            keep = {acc} | set(nx.descendants(self.g, acc))
            for ent in self.entities_for_account(account_id):
                keep |= set(self.playbooks_for([ent]))
            sub = self.g.subgraph(keep)
        else:
            sub = self.g
        nodes = [{"id": n, "type": d.get("type"), "label": d.get("label", n)} for n, d in sub.nodes(data=True)]
        edges = [{"source": u, "target": v, "rel": d.get("rel", "")} for u, v, d in sub.edges(data=True)]
        return {"nodes": nodes, "edges": edges}

    
    def _extract(self, text: str):
        t = f" {_norm(text)} "
        seen: set[tuple[str, str]] = set()
        for etype, terms in LEXICON.items():
            for term in terms:
                if f" {term}" in t:
                    key = (etype, term)
                    if key not in seen:
                        seen.add(key)
                        yield etype, f"{etype}:{term}"
