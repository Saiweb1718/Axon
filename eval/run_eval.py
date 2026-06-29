"""Evaluation harness — measurable business outcomes for the platform.

Method:
  * Replay a labelled portfolio of accounts (eval/cases.json).
  * For each, run the FULL platform (planner -> agents) and take the top action.
  * Compare the platform's top next-best-action category to an expert label
    -> Top-1 NBA accuracy.
  * Simulate the business outcome: NRR and $ retained/expanded WITH the platform
    (correct proactive action taken) vs WITHOUT (no proactive action).

Run:  PYTHONPATH=<axon root> python eval/run_eval.py
Runs fully offline on the stub LLM.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

os.environ.setdefault("LLM_PROVIDER", "stub")

from app import agents  # noqa: F401  (registers agents)
from app.agents.base import Context
from app.config import load_config
from app.llm import get_llm
from app.memory.local import LocalMemory
from app.models import Interaction
from app.orchestrator import Orchestrator

ROOT = Path(__file__).resolve().parent.parent
CASES = json.loads((ROOT / "eval" / "cases.json").read_text(encoding="utf-8"))
CONFIG = load_config(ROOT / "config" / "customer_success.yaml")
LLM = get_llm()


def categorize(action: str) -> str:
    a = action.lower()
    if "roi" in a or "value review" in a:
        return "roi_review"
    if "save play" in a or "usage-decline" in a:
        return "save_play"
    if "expansion" in a or "seat" in a or "upsell" in a:
        return "expansion"
    return "monitor"


def run_case(case: dict) -> dict:
    mem = LocalMemory(playbooks_path=ROOT / "data" / "playbooks.json")
    for it in case["interactions"]:
        mem.remember(Interaction(account_id=case["id"], kind=it["kind"], text=it["text"]))

    def usage_tool(_ctx: Context) -> str:
        u = case.get("usage", "stable")
        mem.remember(Interaction(account_id=case["id"], kind="usage", text=f"Recent usage: {u}"))
        return f"Recent usage: {u}"

    orch = Orchestrator(tools={"recent_usage": usage_tool})
    ctx = Context(account_id=case["id"], goal="Determine the next best action today", memory=mem, llm=LLM, config=CONFIG)
    result = orch.run(ctx)
    recs = result["recommendations"]
    top = recs[0] if recs else {"action": "monitor", "confidence": 0.0}
    return {"category": categorize(top["action"]), "action": top["action"], "confidence": top["confidence"]}


def main() -> None:
    hits = 0
    start_arr = 0.0
    baseline_end = 0.0
    platform_end = 0.0
    churn_prevented = 0.0
    expansion_captured = 0.0
    rows = []

    for case in CASES:
        out = run_case(case)
        expected = case["expected_action"]
        hit = out["category"] == expected
        hits += int(hit)

        arr = float(case["arr"])
        start_arr += arr
        base_retained = arr * (1 - case["churn_prob_no_action"])
        baseline_end += base_retained

        if hit and expected in ("roi_review", "save_play"):
            retained = arr * (1 - case["churn_prob_right_action"])
            churn_prevented += retained - base_retained
            platform_end += retained
        elif hit and expected == "expansion":
            captured = float(case.get("expansion_value", 0))
            expansion_captured += captured
            platform_end += base_retained + captured
        else:
            platform_end += base_retained  # miss or 'monitor' -> same as baseline

        rows.append((case["name"], expected, out["category"], "HIT " if hit else "miss", out["confidence"]))

    n = len(CASES)
    print("\nPer-account next-best-action vs expert label")
    print("-" * 78)
    print(f"{'account':<26}{'expected':<13}{'platform':<13}{'result':<7}{'conf'}")
    for name, exp, got, res, conf in rows:
        print(f"{name:<26}{exp:<13}{got:<13}{res:<7}{conf}")

    summary = {
        "nba_top1_accuracy": round(hits / n, 3),
        "accounts_evaluated": n,
        "nrr_baseline_pct": round(baseline_end / start_arr * 100, 1),
        "nrr_platform_pct": round(platform_end / start_arr * 100, 1),
        "churn_dollars_prevented": round(churn_prevented),
        "expansion_dollars_captured": round(expansion_captured),
    }

    print("\nMeasurable business outcomes")
    print("-" * 78)
    print(f"Top-1 NBA accuracy            : {hits}/{n} = {summary['nba_top1_accuracy']*100:.0f}%")
    print(f"NRR  without platform         : {summary['nrr_baseline_pct']}%")
    print(f"NRR  with platform            : {summary['nrr_platform_pct']}%  "
          f"(+{round(summary['nrr_platform_pct'] - summary['nrr_baseline_pct'], 1)} pts)")
    print(f"Churn $ prevented             : ${summary['churn_dollars_prevented']:,}")
    print(f"Expansion $ captured          : ${summary['expansion_dollars_captured']:,}")

    (ROOT / "eval" / "results.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("\nWrote eval/results.json")


if __name__ == "__main__":
    main()
