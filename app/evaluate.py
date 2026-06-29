from __future__ import annotations

import json
import os
from pathlib import Path

os.environ["LLM_PROVIDER"] = "stub"  # force the deterministic offline provider — a reproducible gate

ROOT = Path(__file__).resolve().parent.parent


def run_eval() -> dict:
    from .agents.base import Context
    from .config import load_config
    from .llm import get_llm
    from .memory.semantic import SemanticMemory
    from .memory.store import Store
    from .models import Feedback, Interaction
    from .orchestrator import Orchestrator

    store = Store(":memory:")
    mem = SemanticMemory(store, playbooks_path=ROOT / "data" / "playbooks.json")
    llm = get_llm()
    config = load_config(ROOT / "config" / "customer_success.yaml")

    seed = json.loads((ROOT / "data" / "accounts.json").read_text(encoding="utf-8"))
    for acc in seed:
        store.upsert_account(acc)
        mem.graph.add_account(acc["id"], acc.get("name", ""))
        for it in acc.get("interactions", []):
            mem.remember(Interaction(account_id=acc["id"], kind=it["kind"], text=it["text"]))

    def usage_tool(ctx: "Context") -> str:
        a = store.get_account(ctx.account_id) or {}
        mem.remember(Interaction(account_id=ctx.account_id, kind="usage", text=f"Recent usage: {a.get('usage', 'stable')}"))
        return f"Recent usage: {a.get('usage', 'stable')}"

    orch = Orchestrator(tools={"recent_usage": usage_tool})

    def run(aid: str) -> dict:
        ctx = Context(account_id=aid, goal="Determine the next best actions for this account today",
                      memory=mem, llm=llm, config=config)
        ctx.bb["query"] = ctx.goal
        return orch.run(ctx)

    cases = [a for a in seed if a.get("expected_action_keywords")]
    hits, mrr_sum, rows = 0, 0.0, []
    for a in cases:
        recs = run(a["id"])["recommendations"]
        kws = [k.lower() for k in a["expected_action_keywords"]]
        rank = next((i + 1 for i, r in enumerate(recs) if any(k in r["action"].lower() for k in kws)), 0)
        hits += 1 if rank == 1 else 0
        mrr_sum += (1.0 / rank) if rank else 0.0
        rows.append({"account": a["name"], "expected": a["expected_action_keywords"],
                     "top_action": recs[0]["action"] if recs else "—",
                     "matched_rank": rank, "top1": rank == 1})

    # learning check: reject the top action on the first case, re-run, confirm change
    learning = None
    if cases:
        a = cases[0]
        before = run(a["id"])["recommendations"]
        if before:
            top = before[0]
            mem.improve(Feedback(recommendation_id=top["id"], account_id=a["id"],
                                 action=top["action"], decision="rejected"))
            after = run(a["id"])["recommendations"]
            learning = {"account": a["name"], "rejected": top["action"],
                        "new_top": after[0]["action"] if after else "—",
                        "changed_after_feedback": bool(after) and after[0]["action"] != top["action"]}

    n = len(cases)
    return {
        "n_cases": n,
        "top1_accuracy": round(hits / n, 3) if n else 0.0,
        "mrr": round(mrr_sum / n, 3) if n else 0.0,
        "learning_check": learning,
        "rows": rows,
        "embeddings": mem.embed.name,
        "llm": llm.name,
    }


if __name__ == "__main__":
    print(json.dumps(run_eval(), indent=2))
