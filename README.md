# Axon — Intelligent Next Best Action Platform

A   reusable agentic decision-intelligence platform  : a dynamic   Planner   orchestrates specialized
agents over a real   memory layer   (semantic vector recall + a knowledge graph + SQLite persistence +
case-based learning) to turn customer interactions and enterprise knowledge into   explainable next
best actions   — with a human in the loop.

---

## 1. Team
| | |
|---|---|
|   Team name : Axon 
|   Team size : 2 
|   Members   : 1.Sriram Saideep (23071A1258 - IT) , email : saideepsriram2005@gmail.com , phone : 9177097582
                2.Siddharth Reddy Gogula (23071A1212 - IT) , email : siddharthreddygogula123@gmail.com , phone : 8008904174
|   GitHub   | https://github.com/Saiweb1718 |

---

## 2. Project overview

  The problem.   In B2B SaaS Customer Success, one manager owns 40+ accounts worth millions. Signals
arrive constantly — meetings, emails, support tickets, usage data — and no human can reason over all
of it for every account, every day. So   churn is caught too late and expansion is missed.  

  What Axon does.   For any account it ingests the interactions, gathers the organization's knowledge,
analyzes the situation,   recommends ranked next best actions  , explains each with evidence and
confidence, lets a human   approve/edit/reject  ,   drafts the action   (a real Gmail draft), and
  learns   from the decision. It is a  platform that decides  — not a chatbot or a RAG app.

  Reusable by design.   The engine is   domain-agnostic   — nothing in `app/` hardcodes "churn." The
entire Customer Success use case lives in `config/customer_success.yaml` + `data/`. Swap those and the
same Planner, agents, and memory run Sales, Staffing, Energy, etc.

  Capabilities  
| Capability | How |
|---|---|
| Dynamic planner orchestration | `planner.py` selects agents from a registry; `orchestrator.py`   re-plans   when info is missing |
| Reusable agents (6) | ingestion · retrieval · analyzer · recommender · explainer · execution — drop a class, `register()`, done |
| Semantic memory | embeddings + cosine recall (not keyword matching) |
| Knowledge graph | entities/relationships +   graph-expansion   (a risk pulls in the playbook that addresses it) |
| Case-based learning | every human decision is embedded; rejected actions are down-ranked next time |
| Explainability | confidence, structured findings, and evidence citations back into memory |
| Human-in-the-loop → execution | approve/edit/reject → drafts a real   Gmail draft   (never auto-sends) |
| Evaluation | `evaluate.py` — top-1 accuracy, MRR, and a before/after learning check |

  Measured outcomes   (`python -m app.evaluate`, reproducible/offline):   top-1 accuracy 100%  ,
  MRR 1.0  ,   learns from feedback: yes   — including a healthy account where the correct answer is
"continue monitoring" (the platform shows restraint).

```
 Experience    React UI:  Portfolio · Account workspace · Memory Explorer · Evaluation
 Orchestration PLANNER ──► plan (which agents) ──► RE-plan on missing info
 Agents        ingestion · retrieval · analyzer · recommender · explainer · execution   (registry)
 Memory        Embeddings + VectorStore | KnowledgeGraph | Decision (case) memory
               └────────────── SQLite (durable source of truth) ──────────────┘
 Config        config/customer_success.yaml + data/   (swap to change domain)
```

---

## 3. GitHub repository

  https://github.com/Saiweb1718  

---

## 4. Setup instructions

  Backend   (Python 3.11+):
```bash
cd axon
python -m venv .venv
.venv\Scripts\activate                 # Windows   (mac/linux: source .venv/bin/activate)
pip install -r requirements.txt
uvicorn app.main:app --reload          # → http://127.0.0.1:8000   (/docs for OpenAPI)
```

  Frontend   (Node 18+):
```bash
cd axon/web
npm install
npm run dev                            # → http://localhost:5173
```

  Run with no server and no keys   (fully offline, deterministic):
```bash
python smoke.py            # full pipeline + the learning loop
python -m app.evaluate     # measurable outcomes (top-1, MRR, learning)
```

  Optional `.env`   (copy from `.env.example`; the app runs offline without it):
```bash
GEMINI_API_KEY=...         # enables real Gemini reasoning (LLM_PROVIDER=auto picks it up)
EMBED_PROVIDER=gemini      # optional: true semantic embeddings (default is the offline hash embedder)
GMAIL_ADDRESS=you@gmail.com        # optional: Approve → real Gmail draft (IMAP App Password)
GMAIL_APP_PASSWORD=xxxxxxxxxxxxxxxx
```

---

## 5. Additional notes

-   Offline-first & resilient.   With no key it runs on a deterministic stub; with a key it uses
    Gemini 2.5 Flash   (thinking disabled for speed). On any quota/error it   falls back to the stub
  per-call  , so a demo never breaks mid-recording.
-   Gemini free-tier quota   is small (~per-model daily cap). For heavy testing, enable billing on the
  Google project — `gemini-flash` is very cheap. The app degrades gracefully if quota runs out.
-   Gmail drafts   use IMAP + a Google   App Password   (Security → 2-Step Verification → App
  passwords; enable IMAP in Gmail). It only   drafts   — it never sends.
-   Persistence:   SQLite (`axon.db`) is the source of truth; the vector store and graph are rebuilt
  from it on boot. `axon.db`, `.venv`, `node_modules`, and `.env` are gitignored.
-   Docs:   [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) (design), [`docs/CONCEPTS.md`](docs/CONCEPTS.md)
  (learn/rebuild it from scratch), [`docs/DEMO_SCRIPT.md`](docs/DEMO_SCRIPT.md) (video script),
  [`docs/diagrams/`](docs/diagrams/) (architecture SVGs).
-   Roadmap:   a `CogneeMemory` backend (the `Memory` method names mirror Cognee's lifecycle) and
  Postgres + pgvector for scale — both drop in behind existing interfaces, no agent changes.
