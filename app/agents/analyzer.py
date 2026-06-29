"""Risk/Opportunity Analyzer — structured findings + missing information.

Each finding is structured: {type, description, severity, urgency, confidence,
evidence} — the reasoning layer judges, the recommender acts. Flagging missing
info (as short machine tags) is what lets the platform re-plan: fetch the gap,
then re-reason, instead of guessing.
"""
from __future__ import annotations

from .base import Agent, Context, register

SYSTEM = (
    "You are a senior Customer Success risk analyst. TASK=ANALYZE. "
    "From the ACCOUNT SIGNALS, return STRICT JSON: "
    "{\"findings\":[{\"type\":\"risk\"|\"opportunity\"|\"gap\",\"description\":str,"
    "\"severity\":\"high\"|\"medium\"|\"low\",\"urgency\":\"high\"|\"medium\"|\"low\","
    "\"confidence\":0-1,\"evidence\":str}], \"missing\":[short_snake_case_tag,...]}. "
    "Base findings ONLY on the account's own signals; use ORG KNOWLEDGE as reference. "
    "For 'missing', emit short machine tags like 'recent_usage', 'renewal_date', 'last_ebr'."
)


class AnalyzerAgent(Agent):
    name = "analyzer"
    description = "Identifies risks, opportunities, and missing information as structured findings."
    inputs = ["context_text", "history_text"]
    outputs = ["analysis", "needs"]

    def run(self, ctx: Context) -> None:
        prompt = (
            "ACCOUNT SIGNALS (this specific customer):\n"
            f"{ctx.bb.get('history_text', '(none)')}\n\n"
            "ORG KNOWLEDGE (reference playbooks / best practices):\n"
            f"{ctx.bb.get('context_text', '')}\n\n"
            "Identify churn risks, expansion opportunities, and any missing information."
        )
        data = ctx.llm.complete_json(SYSTEM, prompt)

        findings = [f for f in data.get("findings", []) if isinstance(f, dict) and f.get("description")]
        for f in findings:  # normalise casing so any model's output renders/derives correctly
            for k in ("type", "severity", "urgency"):
                f[k] = str(f.get(k, "")).strip().lower()
        risks = [f["description"] for f in findings if f["type"] == "risk"]
        opportunities = [f["description"] for f in findings if f["type"] == "opportunity"]
        missing = [m for m in data.get("missing", []) if isinstance(m, str) and m.strip()]

        ctx.bb["analysis"] = {
            "findings": findings,
            "risks": risks,
            "opportunities": opportunities,
            "missing": missing,
        }
        fetched = ctx.bb.get("fetched", [])
        for tag in missing:
            if tag not in fetched and tag not in ctx.needs:
                ctx.needs.append(tag)
        ctx.trace.append(
            f"analyzer: {len(findings)} finding(s) "
            f"({len(risks)} risk / {len(opportunities)} opportunity), missing={missing}"
        )


register(AnalyzerAgent())
