"""Verify the platform over real HTTP routing (FastAPI TestClient)."""
import os

os.environ.setdefault("LLM_PROVIDER", "stub")

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

c = TestClient(app)

print("health  :", c.get("/health").json())
print("agents  :", [a["name"] for a in c.get("/agents").json()])
print("accounts:", [a["id"] for a in c.get("/accounts").json()])

r = c.post("/recommend", json={"account_id": "acme"}).json()
print("recommend(acme) plan :", r["plan"])
top = r["recommendations"][0]
print("top action           :", top["confidence"], top["action"])

rid = next(x for x in r["recommendations"] if "save play" in x["action"].lower())
d = c.post(
    "/decision",
    json={
        "recommendation_id": rid["id"],
        "account_id": "acme",
        "action": rid["action"],
        "decision": "rejected",
    },
).json()
print("decision(reject)     :", d)

r2 = c.post("/recommend", json={"account_id": "acme"}).json()
sp = next(x for x in r2["recommendations"] if "save play" in x["action"].lower())
print("save play after reject:", "conf", sp["confidence"], "rank", sp["rank"], "down_ranked", sp["down_ranked_by_feedback"])
print("HTTP check OK")
