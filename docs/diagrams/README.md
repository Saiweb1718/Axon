# Architecture diagrams

Video-ready SVGs for the demo + architecture walkthrough. Open any `.svg` in a browser
(or drop into slides) — they're self-contained.

| File | What it shows | Narrate in ~30s |
|---|---|---|
| `01-system-architecture.svg` | The full layered platform | "Everything is behind interfaces, so it's layered and swappable. Requests flow top→down — UI → API → Planner → agents → memory → foundations — and the human-in-the-loop returns on the right." |
| `02-recommend-flow.svg` | One `/recommend` request, end to end | "One click runs five agents over a shared blackboard. The **re-plan loop** at the analyzer fetches missing info and re-reasons. The human approves → drafts the Gmail email **and** feeds the decision back to memory to learn." |
| `03-memory-layer.svg` | Vector + graph recall over SQLite | "Writing a signal embeds it for **cosine search** and extracts entities into the **graph**. Recall hits both — vectors find lookalikes, the graph pulls the **playbook that addresses the risk**. SQLite is the source of truth; indexes rebuild on boot." |
| `04-ranker-score.svg` | How the priority score is computed | "Four factors, weighted from the YAML, give a 0–1 score; memory then up/down-ranks by past decisions. Transparent, configurable, and learning-aware — not a black box." |
