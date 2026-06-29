
from __future__ import annotations

from .base import Agent, Context, register


class ExplainerAgent(Agent):
    name = "explainer"
    description = "Attaches supporting evidence and a reasoning trace to each recommendation."
    inputs = ["recommendations", "evidence", "analysis"]
    outputs = ["recommendations"]

    def run(self, ctx: Context) -> None:
        evidence = ctx.bb.get("evidence", [])
        analysis = ctx.bb.get("analysis", {})
        for rec in ctx.bb.get("recommendations", []):
            rec["evidence"] = evidence[:3]
            rec["reasoning_trace"] = analysis
        ctx.trace.append("explainer: attached evidence + reasoning to each recommendation")


register(ExplainerAgent())
