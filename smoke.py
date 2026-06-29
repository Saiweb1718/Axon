"""End-to-end smoke test of the platform — runs fully offline on the stub LLM.

Run:  PYTHONPATH=<axon root> python smoke.py
It exercises: planning, retrieval, analysis, recommendation, the human-in-the-
loop learning loop, and dynamic re-planning — with no server and no API key.
"""
import os

os.environ.setdefault("LLM_PROVIDER", "stub")  # force deterministic offline run

from app.main import RecommendReq, decision, llm, recommend  
from app.models import Feedback  


def show(title: str, result: dict) -> None:
    print("\n" + "=" * 72)
    print(title, f"   (llm={llm.name})")
    print("-" * 72)
    print("Plan:", " -> ".join(result["plan"]))
    print("Reasoning trace:")
    for t in result["trace"]:
        print("   -", t)
    print("Next best actions:")
    for r in result["recommendations"]:
        flag = "   <== down-ranked (learned from rejection)" if r.get("down_ranked_by_feedback") else ""
        print(f"   #{r['rank']}  conf={r['confidence']}  {r['action']}{flag}")
        print(f"          evidence: {[e['source'] for e in r['evidence']]}")


# 1) Acme — churn-risk account
r1 = recommend(RecommendReq(account_id="acme"))
show("ACME CORP  —  initial recommendations (churn risk)", r1)

# 2) Human rejects the save-play -> platform remembers
target = next(x for x in r1["recommendations"] if "save play" in x["action"].lower())
decision(
    Feedback(
        recommendation_id=target["id"],
        account_id="acme",
        action=target["action"],
        decision="rejected",
        note="We tried that recently; it annoyed them.",
    )
)
print(f"\n>>> HUMAN REJECTED: {target['action']}")

# 3) Acme re-run -> the rejected action is now down-ranked
r2 = recommend(RecommendReq(account_id="acme"))
show("ACME CORP  —  after learning from the rejection", r2)

# 4) Globex — expansion account that triggers dynamic re-planning
r3 = recommend(RecommendReq(account_id="globex"))
show("GLOBEX INC  —  expansion + dynamic re-plan (fetched missing usage)", r3)

print("\nSmoke test complete.")
