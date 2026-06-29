
from __future__ import annotations

import time
import uuid
from typing import Any, Optional

from pydantic import BaseModel, Field


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


class Interaction(BaseModel):
    """One raw signal about a customer: a note, email, ticket, CRM update, usage event."""
    id: str = Field(default_factory=lambda: _id("int"))
    account_id: str
    kind: str = "note"          # meeting_note | email | ticket | crm_update | usage | note
    text: str
    ts: float = Field(default_factory=time.time)
    meta: dict[str, Any] = Field(default_factory=dict)


class Evidence(BaseModel):
    """A citation that supports a recommendation. `ref` points back into memory."""
    source: str                 # account_history | org_knowledge | tool:<name>
    ref: str
    snippet: str
    score: float = 0.0          # semantic relevance (cosine); 0 when unscored


class Recommendation(BaseModel):
    id: str = Field(default_factory=lambda: _id("rec"))
    account_id: str
    action: str
    rationale: str
    confidence: float
    factors: dict[str, float] = Field(default_factory=dict)  # impact/urgency/confidence/effort
    score: float = 0.0                                       # composite priority score (0-1)
    priority: str = "MEDIUM"                                 # HIGH | MEDIUM | LOW
    rank: int = 0
    evidence: list[Evidence] = Field(default_factory=list)
    reasoning_trace: dict[str, Any] = Field(default_factory=dict)
    down_ranked_by_feedback: bool = False   # set when memory learned this was rejected here
    status: str = "pending_review"   # pending_review | approved | rejected | edited
    artifact: dict[str, Any] = Field(default_factory=dict)   # execution draft, set on approve


class PlanStep(BaseModel):
    agent: str
    reason: str = ""


class Plan(BaseModel):
    goal: str
    steps: list[PlanStep] = Field(default_factory=list)


class Feedback(BaseModel):
    """A human's decision on a recommendation — the signal the platform learns from."""
    recommendation_id: str
    account_id: str
    action: str
    decision: str               # approved | rejected | edited
    note: str = ""
    edited_action: Optional[str] = None
