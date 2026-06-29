"""FastAPI surface for the platform.

Endpoints
  GET  /health                     liveness + active LLM/embedding providers
  GET  /agents                     the reusable agent catalogue (registry)
  GET  /accounts                   portfolio summary
  POST /accounts                   create a customer
  GET  /accounts/{id}              account + interaction timeline + decisions
  GET  /accounts/{id}/memory       per-account knowledge graph + timeline
  GET  /memory/graph               whole knowledge graph (Memory Explorer)
  POST /memory/search              semantic recall over memory (vector + graph)
  POST /ingest                     remember new interactions (auto-creates account)
  POST /recommend                  planner -> agents -> ranked next best actions
  POST /decision                   human-in-the-loop -> memory.improve (learning)
  GET  /eval                       evaluation harness (measurable outcomes)
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from . import agents  # noqa: F401  (import side effect: registers all agents)
from .agents.base import REGISTRY, Context, registry_manifest
from .config import load_config
from .llm import get_llm
from .integrations.gmail import create_gmail_draft
from .memory.semantic import SemanticMemory
from .memory.store import Store
from .models import Feedback, Interaction

# orchestrator import lives next to planner; keep the existing module
from .orchestrator import Orchestrator

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "axon.db"

# --- platform singletons ---
store = Store(DB_PATH)
memory = SemanticMemory(store, playbooks_path=ROOT / "data" / "playbooks.json")
llm = get_llm()
config = load_config(ROOT / "config" / "customer_success.yaml")

# seed once (first boot) from JSON; afterwards SQLite is the source of truth
if store.count_accounts() == 0:
    seed = json.loads((ROOT / "data" / "accounts.json").read_text(encoding="utf-8"))
    for acc in seed:
        store.upsert_account(acc)
        memory.graph.add_account(acc["id"], acc.get("name", ""))
        for it in acc.get("interactions", []):
            memory.remember(Interaction(account_id=acc["id"], kind=it["kind"], text=it["text"]))


def usage_tool(ctx: Context) -> str:
    """Tool the orchestrator calls when 'recent_usage' is flagged missing."""
    acc = store.get_account(ctx.account_id) or {}
    usage = acc.get("usage", "stable")
    memory.remember(Interaction(account_id=ctx.account_id, kind="usage", text=f"Recent usage: {usage}"))
    return f"Recent usage: {usage}"


orchestrator = Orchestrator(tools={"recent_usage": usage_tool})

app = FastAPI(title="Axon — Intelligent Next Best Action Platform")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


# ----------------------------- platform -----------------------------
@app.get("/health")
def health() -> dict:
    return {"ok": True, "llm": llm.name, "embeddings": memory.embed.name, "domain": config.get("domain")}


@app.get("/agents")
def agents_list() -> list[dict]:
    return registry_manifest()


# ----------------------------- accounts -----------------------------
def _summary(a: dict) -> dict:
    return {"id": a["id"], "name": a["name"], "arr": a["arr"], "renewal": a["renewal"],
            "signals": len(store.interactions(a["id"]))}


@app.get("/accounts")
def accounts() -> list[dict]:
    return [_summary(a) for a in store.all_accounts()]


class AccountIn(BaseModel):
    id: Optional[str] = None
    name: str
    arr: float = 0
    renewal: str = ""
    usage: str = "stable"
    interactions: list[dict] = []


@app.post("/accounts")
def create_account(body: AccountIn) -> dict:
    aid = body.id or re.sub(r"[^a-z0-9]+", "-", body.name.lower()).strip("-") or "account"
    store.upsert_account({"id": aid, "name": body.name, "arr": body.arr,
                          "renewal": body.renewal, "usage": body.usage})
    memory.graph.add_account(aid, body.name)
    for it in body.interactions:
        memory.remember(Interaction(account_id=aid, kind=it.get("kind", "note"), text=it.get("text", "")))
    return {"id": aid, "created": True, "signals": len(store.interactions(aid))}


@app.get("/accounts/{account_id}")
def account_detail(account_id: str) -> dict:
    acc = store.get_account(account_id)
    if not acc:
        raise HTTPException(404, f"unknown account '{account_id}'")
    return {"account": acc,
            "timeline": [i.model_dump() for i in store.interactions(account_id)],
            "decisions": store.decisions(account_id)}


# ----------------------------- memory -----------------------------
@app.get("/accounts/{account_id}/memory")
def account_memory(account_id: str) -> dict:
    if not store.get_account(account_id):
        raise HTTPException(404, f"unknown account '{account_id}'")
    return {"graph": memory.graph_export(account_id),
            "timeline": [i.model_dump() for i in store.interactions(account_id)]}


@app.get("/memory/graph")
def memory_graph(account_id: Optional[str] = None) -> dict:
    return memory.graph_export(account_id)


class SearchIn(BaseModel):
    query: str
    account_id: Optional[str] = None
    k: int = 6


@app.post("/memory/search")
def memory_search(body: SearchIn) -> dict:
    ev = memory.recall(body.query, account_id=body.account_id, k=body.k)
    return {"query": body.query, "results": [e.model_dump() for e in ev]}


# ----------------------------- ingest -----------------------------
class IngestReq(BaseModel):
    account_id: str
    interactions: list[dict]


@app.post("/ingest")
def ingest(req: IngestReq) -> dict:
    if not store.get_account(req.account_id):
        store.upsert_account({"id": req.account_id, "name": req.account_id})
        memory.graph.add_account(req.account_id, req.account_id)
    for it in req.interactions:
        memory.remember(Interaction(account_id=req.account_id, kind=it.get("kind", "note"), text=it.get("text", "")))
    return {"stored": len(req.interactions), "account_id": req.account_id}


# ----------------------------- recommend / decide -----------------------------
class RecommendReq(BaseModel):
    account_id: str
    goal: str = "Determine the next best actions for this account today"


@app.post("/recommend")
def recommend(req: RecommendReq) -> dict:
    if not store.get_account(req.account_id):
        raise HTTPException(404, f"unknown account '{req.account_id}'")
    ctx = Context(account_id=req.account_id, goal=req.goal, memory=memory, llm=llm, config=config)
    ctx.bb["query"] = req.goal
    result = orchestrator.run(ctx)
    for rec in result["recommendations"]:
        store.save_recommendation(rec)
    return result


def draft_execution(account_id: str, action: str) -> dict:
    """Run the Execution agent to draft a ready-to-send artifact for an approved action."""
    acc = store.get_account(account_id) or {}
    ctx = Context(account_id=account_id, goal="execute approved action", memory=memory, llm=llm, config=config)
    ctx.bb["execute_action"] = action
    ctx.bb["account_name"] = acc.get("name", account_id)
    REGISTRY["execution"].run(ctx)
    return ctx.bb.get("artifact", {})


@app.post("/decision")
def decision(fb: Feedback) -> dict:
    memory.improve(fb)
    store.set_status(fb.recommendation_id, fb.decision)
    resp: dict = {
        "ok": True,
        "decision": fb.decision,
        "learned": fb.decision in ("rejected", "approved"),
        "message": ("Recorded — similar actions will be down-ranked for comparable situations."
                    if fb.decision == "rejected" else "Recorded into memory."),
    }
    # Human-in-the-loop → Execution: an approved action is drafted into a real artifact.
    if fb.decision == "approved":
        artifact = draft_execution(fb.account_id, fb.edited_action or fb.action)
        resp["artifact"] = artifact
        # Deliver an email artifact into the user's real Gmail Drafts (draft only — never sends).
        if artifact.get("channel") == "email":
            resp["delivery"] = create_gmail_draft(artifact)
        rec = store.get_recommendation(fb.recommendation_id)
        if rec:
            rec["status"] = "approved"
            rec["artifact"] = artifact
            rec["delivery"] = resp.get("delivery", {})
            store.save_recommendation(rec)
    return resp


# ----------------------------- evaluation -----------------------------
@app.get("/eval")
def eval_endpoint() -> dict:
    from .evaluate import run_eval
    return run_eval()
