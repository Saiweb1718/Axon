from __future__ import annotations

from .base import Agent, Context, register


class RetrievalAgent(Agent):
    name = "retrieval"
    description = "Gathers relevant organizational knowledge and account history from shared memory."
    outputs = ["evidence", "context_text", "history_text"]

    def run(self, ctx: Context) -> None:
        history = ctx.memory.interactions(ctx.account_id)
        history_text = " ".join(i.text for i in history)
        query = f"{ctx.bb.get('query', ctx.goal)} {history_text}".strip()

        evidence = ctx.memory.recall(query, account_id=ctx.account_id, k=8)

        ctx.bb.setdefault("evidence", [])
        ctx.bb["evidence"] += [e.model_dump() for e in evidence]
        ctx.bb["context_text"] = "\n".join(f"- [{e.source}] {e.snippet}" for e in evidence)
        ctx.bb["history_text"] = "\n".join(f"- ({i.kind}) {i.text}" for i in history)
        ctx.trace.append(f"retrieval: pulled {len(evidence)} evidence item(s) across org + account memory")


register(RetrievalAgent())
