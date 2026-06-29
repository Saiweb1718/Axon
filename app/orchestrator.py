
from __future__ import annotations

from typing import Callable

from .agents.base import REGISTRY, Context
from .models import Evidence, Recommendation
from .planner import Planner

# A tool fetches a named piece of missing info and returns a human-readable string.
Tool = Callable[[Context], str]

RE_REASON_STEPS = ["analyzer", "recommender", "explainer"]


class Orchestrator:
    def __init__(self, tools: dict[str, Tool] | None = None) -> None:
        self.planner = Planner()
        self.tools = tools or {}

    def run(self, ctx: Context) -> dict:
        plan = self.planner.plan(ctx)
        for step in plan.steps:
            REGISTRY[step.agent].run(ctx)

        # one dynamic re-plan pass to close information gaps
        if ctx.needs:
            fetched = self._fetch_missing(ctx)
            if fetched:
                ctx.trace.append(f"orchestrator: re-planning after fetching {fetched}")
                for name in RE_REASON_STEPS:
                    if name in REGISTRY:
                        REGISTRY[name].run(ctx)

        return self._materialize(ctx, [s.agent for s in plan.steps])

    def _resolve_tool(self, need: str) -> Tool | None:
        """Match a (possibly free-text) missing-info tag to a tool, robust to LLM phrasing."""
        if need in self.tools:
            return self.tools[need]
        nl = need.lower()
        for key, fn in self.tools.items():
            noun = key.split("_")[-1]
            if key in nl or (len(noun) > 3 and noun in nl):
                return fn
        return None

    def _fetch_missing(self, ctx: Context) -> list[str]:
        fetched: list[str] = []
        for need in list(ctx.needs):
            tool = self._resolve_tool(need)
            if not tool:
                continue
            info = tool(ctx)
            # feed the fetched fact into BOTH the reference context and the account
            # signals, so the re-run analyzer treats the gap as closed.
            ctx.bb["context_text"] = ctx.bb.get("context_text", "") + f"\n- [tool:{need}] {info}"
            ctx.bb["history_text"] = ctx.bb.get("history_text", "") + f"\n- (tool:{need}) {info}"
            ctx.bb.setdefault("evidence", []).append(
                Evidence(source=f"tool:{need}", ref=need, snippet=info).model_dump()
            )
            fetched.append(need)
        if fetched:
            ctx.bb.setdefault("fetched", []).extend(fetched)
            ctx.needs = [n for n in ctx.needs if n not in fetched]
        return fetched

    def _materialize(self, ctx: Context, plan_steps: list[str]) -> dict:
        recs: list[Recommendation] = []
        for r in ctx.bb.get("recommendations", []):
            recs.append(
                Recommendation(
                    account_id=ctx.account_id,
                    action=r["action"],
                    rationale=r.get("rationale", ""),
                    confidence=r.get("confidence", 0.5),
                    factors=r.get("factors", {}),
                    score=r.get("score", r.get("confidence", 0.5)),
                    priority=r.get("priority", "MEDIUM"),
                    rank=r.get("rank", 0),
                    evidence=[Evidence(**e) for e in r.get("evidence", [])],
                    reasoning_trace=r.get("reasoning_trace", {}),
                    down_ranked_by_feedback=r.get("down_ranked_by_feedback", False),
                )
            )
        return {
            "account_id": ctx.account_id,
            "goal": ctx.goal,
            "plan": plan_steps,
            "trace": ctx.trace,
            "recommendations": [r.model_dump() for r in recs],
        }
