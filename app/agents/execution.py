
from __future__ import annotations

from .base import Agent, Context, register

SYSTEM = (
    "You are an execution assistant for a Customer Success Manager. TASK=EXECUTE. "
    "Given an approved action and the account context, draft the artifact to carry it out, "
    "addressed to the relevant stakeholder and referencing the account by name and the action's specifics. "
    "Return STRICT JSON {\"channel\":\"email\"|\"crm_task\"|\"calendar\",\"title\":str,"
    "\"recipient\":str,\"body\":str,\"due_in_days\":int}. Professional and concise."
)


class ExecutionAgent(Agent):
    name = "execution"
    description = "Drafts a ready-to-send artifact (email, CRM task, or calendar invite) for an approved action."
    inputs = ["execute_action"]
    outputs = ["artifact"]

    def run(self, ctx: Context) -> None:
        action = ctx.bb.get("execute_action", "")
        name = ctx.bb.get("account_name", ctx.account_id)
        history = "\n".join(f"- ({i.kind}) {i.text}" for i in ctx.memory.interactions(ctx.account_id))
        prompt = (
            f"Account: {name}\n"
            f"Approved action: {action}\n\n"
            f"Account context:\n{history or '(no prior signals)'}\n\n"
            f"Draft the artifact — greet the relevant stakeholder, reference {name} by name and the action's specifics."
        )
        art = ctx.llm.complete_json(SYSTEM, prompt)
        if not isinstance(art, dict) or not art.get("channel"):
            art = _fallback(action, name)
        ctx.bb["artifact"] = art
        ctx.trace.append(f"execution: drafted a {art.get('channel', 'artifact')} for '{action}'")


def _lc(s: str) -> str:
    return (s[:1].lower() + s[1:]) if s else s


def _fallback(action: str, name: str) -> dict:
    a, act = action.lower(), action.rstrip(".")
    if any(k in a for k in ("review", "meeting", "ebr", "call", "schedule")):
        return {"channel": "calendar", "title": f"{name}: {act[:60]}", "recipient": "Champion / economic buyer",
                "body": f"Proposing a 30-minute session with {name} to {_lc(act)}. Agenda: value delivered, open "
                        f"risks, and next steps. Two time options to follow.", "due_in_days": 5}
    if any(k in a for k in ("expansion", "quote", "pricing", "seat", "upsell")):
        return {"channel": "crm_task", "title": f"{name} — prepare expansion quote", "recipient": "Account Executive",
                "body": f"Build a seat-expansion / volume-pricing quote for {name} to support: {act}.", "due_in_days": 3}
    if any(k in a for k in ("email", "summary", "value", "send")):
        return {"channel": "email", "title": f"{name}: value summary ahead of renewal", "recipient": "Champion",
                "body": f"Hi,\n\nAhead of {name}'s renewal I'd like to {_lc(act)} — covering the outcomes delivered, "
                        f"adoption, and time saved this year. Happy to walk your finance team through it.\n\nBest,\nYour CSM",
                "due_in_days": 2}
    return {"channel": "crm_task", "title": f"{name}: {act[:60]}", "recipient": "Account owner",
            "body": f"Next best action for {name}: {act}. Execute and log the outcome.", "due_in_days": 3}


register(ExecutionAgent())
