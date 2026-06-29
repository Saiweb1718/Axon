from __future__ import annotations

import imaplib
import os
import time
from email.message import EmailMessage


def gmail_configured() -> bool:
    return bool(os.environ.get("GMAIL_ADDRESS") and os.environ.get("GMAIL_APP_PASSWORD"))


def create_gmail_draft(artifact: dict) -> dict:
    """Append an email artifact to Gmail Drafts. Returns a status dict (never raises)."""
    addr = (os.environ.get("GMAIL_ADDRESS") or "").strip()
    pw = (os.environ.get("GMAIL_APP_PASSWORD") or "").replace(" ", "")  # app passwords display with spaces
    if not (addr and pw):
        return {"channel": "gmail_draft", "created": False,
                "reason": "Gmail not configured (set GMAIL_ADDRESS + GMAIL_APP_PASSWORD in .env)"}

    # Safety: drafts are addressed to your own inbox by default — never a real customer domain.
    to = os.environ.get("GMAIL_DRAFT_TO", addr)
    subject = artifact.get("title") or "Customer Success follow-up"
    body = artifact.get("body") or ""
    intended = artifact.get("recipient")
    if intended:
        body = f"[Intended recipient: {intended} — re-address before sending]\n\n{body}"

    msg = EmailMessage()
    msg["From"] = addr
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)

    try:
        imap = imaplib.IMAP4_SSL("imap.gmail.com")
        imap.login(addr, pw)
        imap.append('"[Gmail]/Drafts"', r"(\Draft)", imaplib.Time2Internaldate(time.time()), msg.as_bytes())
        imap.logout()
        return {"channel": "gmail_draft", "created": True, "to": to, "subject": subject}
    except Exception as exc:  # auth/IMAP/network — degrade gracefully
        return {"channel": "gmail_draft", "created": False, "reason": str(exc)[:180]}
