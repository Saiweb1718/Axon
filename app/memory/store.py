
from __future__ import annotations

import json
import sqlite3
import threading
import time
from pathlib import Path

from ..models import Feedback, Interaction


class Store:
    def __init__(self, db_path: str | Path) -> None:
        self.db = sqlite3.connect(str(db_path), check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self._lock = threading.Lock()
        self._init()

    def _init(self) -> None:
        with self._lock:
            self.db.executescript(
                """
                CREATE TABLE IF NOT EXISTS accounts(
                    id TEXT PRIMARY KEY, name TEXT, arr REAL, renewal TEXT, usage TEXT, meta TEXT);
                CREATE TABLE IF NOT EXISTS interactions(
                    id TEXT PRIMARY KEY, account_id TEXT, kind TEXT, text TEXT, ts REAL);
                CREATE TABLE IF NOT EXISTS decisions(
                    id INTEGER PRIMARY KEY AUTOINCREMENT, account_id TEXT, action TEXT,
                    decision TEXT, note TEXT, context TEXT, ts REAL);
                CREATE TABLE IF NOT EXISTS recommendations(
                    id TEXT PRIMARY KEY, account_id TEXT, payload TEXT, status TEXT, ts REAL);
                """
            )
            self.db.commit()

    # ---- accounts ----
    def upsert_account(self, acc: dict) -> None:
        with self._lock:
            self.db.execute(
                "INSERT INTO accounts(id,name,arr,renewal,usage,meta) VALUES(?,?,?,?,?,?) "
                "ON CONFLICT(id) DO UPDATE SET name=excluded.name, arr=excluded.arr, "
                "renewal=excluded.renewal, usage=excluded.usage, meta=excluded.meta",
                (acc["id"], acc.get("name", acc["id"]), acc.get("arr"), acc.get("renewal"),
                 acc.get("usage", "stable"), json.dumps(acc.get("meta", {}))),
            )
            self.db.commit()

    def get_account(self, account_id: str) -> dict | None:
        row = self.db.execute("SELECT * FROM accounts WHERE id=?", (account_id,)).fetchone()
        return _acc(row) if row else None

    def all_accounts(self) -> list[dict]:
        rows = self.db.execute("SELECT * FROM accounts ORDER BY arr DESC").fetchall()
        return [_acc(r) for r in rows]

    def count_accounts(self) -> int:
        return int(self.db.execute("SELECT COUNT(*) FROM accounts").fetchone()[0])

    # ---- interactions ----
    def add_interaction(self, it: Interaction) -> None:
        with self._lock:
            self.db.execute(
                "INSERT OR REPLACE INTO interactions(id,account_id,kind,text,ts) VALUES(?,?,?,?,?)",
                (it.id, it.account_id, it.kind, it.text, it.ts),
            )
            self.db.commit()

    def interactions(self, account_id: str) -> list[Interaction]:
        rows = self.db.execute(
            "SELECT * FROM interactions WHERE account_id=? ORDER BY ts", (account_id,)
        ).fetchall()
        return [_int(r) for r in rows]

    def all_interactions(self) -> list[Interaction]:
        return [_int(r) for r in self.db.execute("SELECT * FROM interactions ORDER BY ts").fetchall()]

    def delete_interaction(self, ref: str) -> None:
        with self._lock:
            self.db.execute("DELETE FROM interactions WHERE id=?", (ref,))
            self.db.commit()

    # ---- decisions ----
    def add_decision(self, fb: Feedback, context: str) -> None:
        with self._lock:
            self.db.execute(
                "INSERT INTO decisions(account_id,action,decision,note,context,ts) VALUES(?,?,?,?,?,?)",
                (fb.account_id, fb.action, fb.decision, fb.note, context, time.time()),
            )
            self.db.commit()

    def decisions(self, account_id: str | None = None) -> list[dict]:
        if account_id:
            rows = self.db.execute(
                "SELECT * FROM decisions WHERE account_id=? ORDER BY ts", (account_id,)
            ).fetchall()
        else:
            rows = self.db.execute("SELECT * FROM decisions ORDER BY ts").fetchall()
        return [dict(r) for r in rows]

    # ---- recommendations ----
    def save_recommendation(self, rec: dict) -> None:
        with self._lock:
            self.db.execute(
                "INSERT OR REPLACE INTO recommendations(id,account_id,payload,status,ts) VALUES(?,?,?,?,?)",
                (rec["id"], rec["account_id"], json.dumps(rec), rec.get("status", "pending_review"), time.time()),
            )
            self.db.commit()

    def set_status(self, rec_id: str, status: str) -> None:
        with self._lock:
            self.db.execute("UPDATE recommendations SET status=? WHERE id=?", (status, rec_id))
            self.db.commit()

    def get_recommendation(self, rec_id: str) -> dict | None:
        row = self.db.execute("SELECT payload FROM recommendations WHERE id=?", (rec_id,)).fetchone()
        return json.loads(row["payload"]) if row else None


def _acc(r: sqlite3.Row) -> dict:
    return {"id": r["id"], "name": r["name"], "arr": r["arr"], "renewal": r["renewal"],
            "usage": r["usage"], "meta": json.loads(r["meta"] or "{}")}


def _int(r: sqlite3.Row) -> Interaction:
    return Interaction(id=r["id"], account_id=r["account_id"], kind=r["kind"], text=r["text"], ts=r["ts"])
