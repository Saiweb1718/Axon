from __future__ import annotations

import json

from .base import Agent, Context, register

SYSTEM = (
    "You are a Customer Success strategist. TASK=RECOMMEND. "
    "Propose candidate next best actions and score EACH on four factors in [0,1]: "
    "impact (business value if it works), urgency (time-sensitivity), confidence "
    "(likelihood it's the right call given the evidence), effort (cost to execute). "
    "Return STRICT JSON {\"recommendations\":[{\"action\":str,\"rationale\":str,"
    "\"impact\":0-1,\"urgency\":0-1,\"confidence\":0-1,\"effort\":0-1}]}. "
    "Base everything on the ACCOUNT's own signals; include a 'continue monitoring' "
    "option when no action is warranted."
)

DEFAULT_WEIGHTS = {"impact": 0.35, "urgency": 0.30, "confidence": 0.25, "effort": 0.10}
DEFAULT_THRESHOLDS = {"high": 0.70, "medium": 0.45}
DEFAULT_LEARNED = {"rejected_penalty": 0.45, "approved_boost": 1.10}


class RecommenderAgent(Agent):
    name = "recommender"
    description = "Scores and ranks next best actions on impact/urgency/confidence/effort, adjusted by learned feedback."
    inputs = ["analysis", "context_text"]
    outputs = ["recommendations"]

    def run(self, ctx: Context) -> None:
        cfg = (ctx.config or {}).get("ranker", {})
        weights = {**DEFAULT_WEIGHTS, **cfg.get("weights", {})}
        thresholds = {**DEFAULT_THRESHOLDS, **cfg.get("priority_thresholds", {})}
        learned_cfg = {**DEFAULT_LEARNED, **cfg.get("learned", {})}

        analysis = ctx.bb.get("analysis", {})
        cases = ctx.memory.recall_decisions(
            f"{json.dumps(analysis)} {ctx.bb.get('context_text', '')}", k=5
        )
        rejected_cases = {c["action"].lower() for c in cases if c["decision"] == "rejected"}
        approved_cases = {c["action"].lower() for c in cases if c["decision"] == "approved"}
        rejected_here = [a.lower() for a in ctx.memory.rejected_actions(ctx.account_id)]
        if cases:
            ctx.trace.append(f"recommender: recalled {len(cases)} comparable past decision(s) from memory")

        cases_text = "\n".join(f"- a human {c['decision']} \"{c['action']}\"" for c in cases) \
            or "- (no comparable past decisions yet)"
        prompt = (
            f"Analysis: {json.dumps(analysis)}\n\n"
            f"Context:\n{ctx.bb.get('context_text', '')}\n\n"
            f"Past human decisions on similar situations:\n{cases_text}\n\n"
            f"Propose and score the candidate next best actions."
        )
        data = ctx.llm.complete_json(SYSTEM, prompt)

        norm = weights["impact"] + weights["urgency"] + weights["confidence"]
        scored = []
        for r in data.get("recommendations", []):
            action = (r.get("action") or "").strip()
            if not action:
                continue
            factors = {
                "impact": _f(r.get("impact"), 0.5),
                "urgency": _f(r.get("urgency"), 0.5),
                "confidence": _f(r.get("confidence"), 0.5),
                "effort": _f(r.get("effort"), 0.5),
            }
            base = (
                weights["impact"] * factors["impact"]
                + weights["urgency"] * factors["urgency"]
                + weights["confidence"] * factors["confidence"]
                - weights["effort"] * factors["effort"]
            ) / norm
            base = max(0.0, min(1.0, base))

            al, learned = action.lower(), False
            if _matches(al, rejected_here) or _matches(al, rejected_cases):
                base *= learned_cfg["rejected_penalty"]
                learned = True
                ctx.trace.append(f"recommender: down-ranked '{action}' — similar to a human-rejected action")
            elif _matches(al, approved_cases):
                base = min(1.0, base * learned_cfg["approved_boost"])
                ctx.trace.append(f"recommender: boosted '{action}' — similar to a human-approved action")

            scored.append((base, action, r.get("rationale", ""), factors, learned))

        scored.sort(key=lambda x: -x[0])
        ctx.bb["recommendations"] = [
            {
                "action": action,
                "rationale": rationale,
                "confidence": round(factors["confidence"], 2),
                "factors": {k: round(v, 2) for k, v in factors.items()},
                "score": round(score, 2),
                "priority": _priority(score, thresholds),
                "rank": i + 1,
                "down_ranked_by_feedback": learned,
            }
            for i, (score, action, rationale, factors, learned) in enumerate(scored)
        ]
        ctx.trace.append(
            f"recommender: ranked {len(scored)} action(s) by weighted impact/urgency/confidence/effort"
        )


def _f(value, default: float) -> float:
    try:
        return max(0.0, min(1.0, float(value)))
    except (TypeError, ValueError):
        return default


def _matches(action: str, pool) -> bool:
    return any(p and (p in action or action in p) for p in pool)


def _priority(score: float, thresholds: dict) -> str:
    if score >= thresholds["high"]:
        return "HIGH"
    if score >= thresholds["medium"]:
        return "MEDIUM"
    return "LOW"


register(RecommenderAgent())
