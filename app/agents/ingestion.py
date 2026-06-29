
from __future__ import annotations

from ..models import Interaction
from .base import Agent, Context, register


class IngestionAgent(Agent):
    name = "ingestion"
    description = "Normalizes raw interactions (notes, emails, tickets, CRM updates) into memory."
    outputs = ["ingested"]

    def run(self, ctx: Context) -> None:
        raw = ctx.bb.get("raw_interactions", [])
        count = 0
        for item in raw:
            ctx.memory.remember(
                Interaction(account_id=ctx.account_id, kind=item.get("kind", "note"), text=item.get("text", ""))
            )
            count += 1
        ctx.bb["ingested"] = count
        ctx.trace.append(f"ingestion: stored {count} new interaction(s)")


register(IngestionAgent())
