
from __future__ import annotations

import json

from .agents.base import Context, registry_manifest
from .models import Plan, PlanStep

SYSTEM = (
    "You are the Planner of an agentic decision platform. TASK=PLAN. "
    "Given a goal and a catalogue of available agents, return STRICT JSON "
    "{\"steps\":[\"agent_name\", ...]} choosing and ordering ONLY the agents needed "
    "to achieve the goal. Do not invent agent names."
)

DEFAULT_PLAN = ["retrieval", "analyzer", "recommender", "explainer"]


class Planner:
    def plan(self, ctx: Context) -> Plan:
        manifest = registry_manifest()
        valid = {m["name"] for m in manifest}
        prompt = (
            f"Goal: {ctx.goal}\n\n"
            f"Available agents:\n{json.dumps(manifest, indent=2)}"
        )
        data = ctx.llm.complete_json(SYSTEM, prompt)
        steps = data.get("steps") or DEFAULT_PLAN
        steps = [s for s in steps if s in valid] or DEFAULT_PLAN
        ctx.trace.append(f"planner: selected plan = {steps}")
        return Plan(goal=ctx.goal, steps=[PlanStep(agent=s) for s in steps])
