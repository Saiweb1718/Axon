# offline 
from __future__ import annotations

import json

from .base import LLMProvider


class StubProvider(LLMProvider):
    name = "stub"

    def complete(self, system: str, prompt: str) -> str:
        task = _task(system)
        p = prompt.lower()

        if task == "PLAN":
            return json.dumps({"steps": ["retrieval", "analyzer", "recommender", "explainer"]})

        if task == "ANALYZE":
            sig = _between(p, "account signals", "org knowledge")  # judge on the account, not the playbooks
            findings, missing = [], []
            if _usage_down(sig):
                findings.append({"type": "risk", "description": "Adoption is declining (usage down), a leading churn indicator.",
                                 "severity": "high", "urgency": "high", "confidence": 0.85, "evidence": "usage trend"})
            if "renew" in sig:
                findings.append({"type": "risk", "description": "Renewal is approaching while account sentiment is negative.",
                                 "severity": "high", "urgency": "high", "confidence": 0.8, "evidence": "renewal date + sentiment"})
            if "roi" in sig or "justif" in sig or "cost" in sig:
                findings.append({"type": "risk", "description": "A stakeholder doubts the product's ROI / cost justification.",
                                 "severity": "high", "urgency": "medium", "confidence": 0.82, "evidence": "stakeholder ROI concern"})
            if "ticket" in sig or "confus" in sig:
                findings.append({"type": "risk", "description": "Support ticket spike signals friction with recent changes.",
                                 "severity": "medium", "urgency": "medium", "confidence": 0.7, "evidence": "ticket spike"})
            if "seat" in sig or "licen" in sig or "90%" in sig or "more access" in sig:
                findings.append({"type": "opportunity", "description": "Team is near its seat/licence limit — expansion opportunity.",
                                 "severity": "medium", "urgency": "medium", "confidence": 0.8, "evidence": "seat utilisation"})
            if "sub-team" in sig or "new seats" in sig or "volume pricing" in sig:
                findings.append({"type": "opportunity", "description": "Customer plans to add teams — proactive upsell opening.",
                                 "severity": "medium", "urgency": "low", "confidence": 0.78, "evidence": "expansion intent"})
            if not _has_usage(sig):
                missing.append("recent_usage")
            return json.dumps({"findings": findings, "missing": missing})

        if task == "RECOMMEND":
            an = _between(p, "analysis:", "context")  # recommend from the analysis, not raw context
            recs = []
            if "roi" in an or "value" in an or "justif" in an:
                recs.append({"action": "Schedule an executive value/ROI review with the customer's economic buyer",
                             "rationale": "Directly addresses the stated ROI concern with evidence of delivered value before renewal.",
                             "impact": 0.9, "urgency": 0.9, "confidence": 0.86, "effort": 0.3})
            if _usage_down(an):
                recs.append({"action": "Trigger the Usage-Decline save play (re-onboarding + champion check-in)",
                             "rationale": "Re-engages users and reverses the adoption drop that precedes churn.",
                             "impact": 0.7, "urgency": 0.6, "confidence": 0.78, "effort": 0.5})
            if "seat" in an or "licen" in an or "expansion" in an or "upsell" in an or "sub-team" in an:
                recs.append({"action": "Propose a seat expansion / volume-pricing quote to the champion",
                             "rationale": "Account is near its seat limit and signalling growth — a clean expansion motion.",
                             "impact": 0.85, "urgency": 0.6, "confidence": 0.7, "effort": 0.3})
            if not recs:
                recs.append({"action": "Continue monitoring — no action needed today",
                             "rationale": "No material risk or opportunity detected in current signals.",
                             "impact": 0.2, "urgency": 0.1, "confidence": 0.55, "effort": 0.1})
            return json.dumps({"recommendations": recs})

        if task == "EXECUTE":
            name = _orig_between(prompt, p, "account:", "approved action") or "the account"
            act = _orig_between(prompt, p, "approved action:", "account context") or "the recommended next step"
            al, act_t = act.lower(), act.rstrip(".")
            if any(k in al for k in ("review", "meeting", "ebr", "call", "schedule")):
                ch, rcpt, due = "calendar", "Champion / economic buyer", 5
                title = f"{name}: {act_t[:56]}"
                body = (f"Proposing a 30-minute session with {name} to {_lc(act_t)}. Agenda: value delivered, "
                        f"open risks, and the path to renewal. Two time options to follow.")
            elif any(k in al for k in ("seat", "expansion", "quote", "pricing", "upsell")):
                ch, rcpt, due = "crm_task", "Account Executive", 3
                title = f"{name} — prepare expansion quote"
                body = (f"Build a seat-expansion / volume-pricing quote for {name} to support: {act_t}. "
                        f"The champion has signalled growth and is near the licence limit.")
            elif any(k in al for k in ("email", "summary", "value", "send")):
                ch, rcpt, due = "email", "Champion", 2
                title = f"{name}: value summary ahead of renewal"
                body = (f"Hi,\n\nAhead of {name}'s renewal I'd like to {_lc(act_t)} — covering the outcomes delivered, "
                        f"adoption, and time saved this year. Happy to walk your finance team through it.\n\nBest,\nYour CSM")
            else:
                ch, rcpt, due = "crm_task", "Account owner", 3
                title = f"{name}: {act_t[:56]}"
                body = f"Next best action for {name}: {act_t}. Execute and log the outcome."
            return json.dumps({"channel": ch, "title": title, "recipient": rcpt, "body": body, "due_in_days": due})

        return "{}"


def _task(system: str) -> str:
    for t in ("PLAN", "ANALYZE", "RECOMMEND", "EXECUTE"):
        if f"TASK={t}" in system:
            return t
    return ""


def _between(text: str, start: str, end: str) -> str:
    """Return the slice of `text` between markers; whole text if start missing."""
    lo = text.find(start)
    if lo == -1:
        return text
    lo += len(start)
    hi = text.find(end, lo)
    return text[lo:hi] if hi != -1 else text[lo:]


def _orig_between(original: str, lower: str, start: str, end: str) -> str:
    """Like _between but locates markers case-insensitively and slices the ORIGINAL text,
    so extracted names/actions keep their original capitalisation for the draft."""
    lo = lower.find(start)
    if lo == -1:
        return ""
    lo += len(start)
    hi = lower.find(end, lo)
    return (original[lo:hi] if hi != -1 else original[lo:]).strip()


def _lc(s: str) -> str:
    return (s[:1].lower() + s[1:]) if s else s


def _has_usage(s: str) -> bool:
    return "usage" in s or "utilis" in s or "utiliz" in s


def _usage_down(s: str) -> bool:
    return ("usage" in s or "adoption" in s or "active user" in s) and (
        "drop" in s or "down" in s or "declin" in s or "decreas" in s
    )
