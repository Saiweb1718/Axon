# Axon — Intelligent Next Best Action Platform

A **reusable agentic decision-intelligence platform**. A dynamic **Planner** orchestrates
specialized agents over a real **memory layer** (semantic vector recall **+** a knowledge
graph **+** SQLite persistence **+** case-based learning) to turn customer interactions and
enterprise knowledge into **explainable next best actions** — with a human in the loop.

The engine is **domain-agnostic**; the demo runs a **B2B SaaS Customer Success** use case
(prevent churn, find expansion). Swap `config/` + `data/` to point the same engine at a new domain.

> Runs fully **offline** — no API key, no GPU, no torch. Real LLM (Gemini) and real
> transformer embeddings are drop-in upgrades behind the same interfaces.

---

## What makes it real 

| Capability | How it's implemented |
|---|---|
| **Dynamic planner orchestration** | `planner.py` asks the LLM to choose agents from the registry; `orchestrator.py` **re-plans** when an agent flags missing info |
| **Reusable agents + tools** | `agents/` — drop a class in, `register()` it, the planner discovers it via the manifest. No engine change |
| **Semantic memory** | `memory/embeddings.py` + `vectorstore.py` — embeddings + cosine recall (not keyword matching) |
| **Knowledge graph** | `memory/graph.py` — entities/relationships per account + org-wide; **graph-expansion** recall pulls the playbook that *addresses* a matched risk |
| **Persistence** | `memory/store.py` — SQLite; accounts/interactions/decisions/recs survive restarts; vectors+graph rebuilt from it |
| **Case-based learning** | every human decision is embedded; `recall_decisions` surfaces how similar situations were handled, and rejected actions are down-ranked |
| **Explainability** | each recommendation carries confidence, a reasoning trace, and evidence citations back into memory |
| **Human-in-the-loop** | approve / edit / reject in the UI → `memory.improve` → the next run visibly changes |
| **Evaluation** | `evaluate.py` — top-1 accuracy, MRR, and a before/after learning check on a clean store |

---

## Quickstart

**Backend** (Python 3.11+):
```bash
cd axon
python -m venv .venv && .venv\Scripts\activate      # Windows  (mac/linux: source .venv/bin/activate)
pip install -r requirements.txt
uvicorn app.main:app --reload                        # http://127.0.0.1:8000  (/docs for OpenAPI)
```

**Frontend** (Node 18+):
```bash
cd axon/web
npm install
npm run dev                                          # http://localhost:5173
```

**Verify with no server and no keys:**
```bash
python smoke.py            # full pipeline + the learning loop, fully offline
python -m app.evaluate     # measurable outcomes (top-1, MRR, learning check)
```

---

## The platform in one picture

```
 Experience    React UI:  Portfolio · Account workspace · Memory Explorer · Evaluation
                                          │ REST
 Orchestration PLANNER ──► plan (which agents, what order) ──► RE-plan on missing info
                                          │
 Agents        ingestion · retrieval · analyzer · recommender · explainer   (registry)
                                          │
 Memory        Embeddings + VectorStore   |   KnowledgeGraph   |   Decision (case) memory
               └──────────────  SQLite  (durable source of truth)  ──────────────┘
                                          │
 Config        config/customer_success.yaml  +  data/   (swap to change domain)
```

Two interfaces are the backbone — everything depends on these, never on a vendor:

```python
class LLMProvider:        complete(system, prompt) -> str      # stub ↔ Gemini ↔ Claude
class EmbeddingProvider:  embed(text) -> vector                # hash-local ↔ Gemini
class Memory:             remember · recall · improve · forget # SemanticMemory ↔ Cognee
```

---

## API

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | liveness + active LLM/embedding providers |
| GET | `/agents` | the reusable agent catalogue (registry) |
| GET | `/accounts` · POST `/accounts` | portfolio summary · create a customer |
| GET | `/accounts/{id}` · `/accounts/{id}/memory` | timeline + decisions · per-account graph |
| GET | `/memory/graph` · POST `/memory/search` | knowledge graph · semantic recall |
| POST | `/ingest` | remember interactions (auto-creates the account) |
| POST | `/recommend` · `/decision` | planner → next best actions · human-in-the-loop |
| GET | `/eval` | run the evaluation harness |

---

## Measured outcomes (`python -m app.evaluate`)

Replays the labelled seed portfolio through the **full** platform on a clean, in-memory store:

| Metric | Result |
|---|---|
| Top-1 next-best-action accuracy | **100%** (3/3 labelled cases) |
| Mean reciprocal rank (MRR) | **1.0** |
| Learns from feedback | **Yes** — after a rejection the top recommendation changes |

The cases include a **healthy** account whose correct answer is *"continue monitoring"* — the
platform recommends **restraint**, not a busy-work action. Numbers are reproducible offline.

---

## Demo script (5 min)
1. **Portfolio** → add a customer; see KPIs + the 5 reusable agents.
2. **Account** → *Run next best actions* on Acme → ranked actions with confidence + evidence + the plan + reasoning trace.
3. **Reject** the save-play → it re-runs and the action is **down-ranked** (memory learned).
4. **Memory Explorer** → the 48-node knowledge graph + semantic search over memory.
5. **Evaluation** → top-1 accuracy, MRR, and the learning check.

See **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** for the design, **[docs/CONCEPTS.md](docs/CONCEPTS.md)**
to learn the ideas from scratch (so you can rebuild it yourself), and **[docs/DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md)**
for the minute-by-minute demo + architecture walkthrough.

---

## Extending it (the reusability story)
- **New agent:** add a class in `app/agents/`, `register()` it, import it in `__init__.py` — the planner uses it immediately (it shows up in `GET /agents`).
- **New domain:** add a YAML in `config/` + seed `data/`. The engine never hardcodes "churn".
- **Real models:** set `GEMINI_API_KEY`, `LLM_PROVIDER=gemini`, `EMBED_PROVIDER=gemini`.
- **Cognee (Phase 2):** implement `CogneeMemory(Memory)` and construct it instead of `SemanticMemory` — agents don't change.
