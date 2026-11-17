"""Email tools via IMAP (read-only). Inert until configured in config.yaml:

email:
  imap_host: imap.gmail.com
  imap_user: you@example.com
  imap_password: your-app-password   # Gmail: App Passwords, not your login password
  imap_port: 993
"""
import imaplib
import email as _email
from email.header import decode_header
from backend import config

CFG = config.CONFIG


def _conn():
    e = CFG.get("email", {})
    host, user, pw = e.get("imap_host", ""), e.get("imap_user", ""), e.get("imap_password", "")
    if not host or not user or not pw:
        return None
    try:
        conn = imaplib.IMAP4_SSL(host, int(e.get("imap_port", 993)))
        conn.login(user, pw)
        return conn
    except Exception:
        return None


def _clean(raw: str) -> str:
    parts = decode_header(raw or "")
    out = []
    for text, enc in parts:
        if isinstance(text, bytes):
            out.append(text.decode(enc or "utf-8", errors="ignore"))
        else:
            out.append(text)
    return "".join(out).strip()


def check_email() -> str:
    conn = _conn()
    if conn is None:
        return ("Email is not configured. Set email.imap_host / imap_user / imap_password "
                "(Gmail: use an App Password) in config.yaml.")
    try:
        conn.select("INBOX", readonly=True)
        status, data = conn.search(None, "UNSEEN")
        unseen_ids = data[0].split() if status == "OK" else []
        count = len(unseen_ids)
        lines = [f"You have {count} unread email(s)."]
        for num in unseen_ids[-3:]:
            status, msg_data = conn.fetch(num, "(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT)])")
            if status != "OK":
                continue
            msg = _email.message_from_bytes(msg_data[0][1])
            lines.append(f"- {_clean(msg.get('Subject', '(no subject)'))} — from {_clean(msg.get('From', '?'))}")
        conn.logout()
        return "\n".join(lines)
    except Exception as e:
        return f"Could not read email: {e}"
