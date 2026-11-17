"""Quick capture notes — local, instant, offline."""
import sqlite3
import time
from backend import config

_DB = None


def _conn():
    global _DB
    if _DB is None:
        _DB = config.CONFIG["_data_dir"] + "/jarvis.db"
        with sqlite3.connect(_DB) as c:
            c.execute("""CREATE TABLE IF NOT EXISTS notes(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,
                ts REAL NOT NULL
            )""")
    return sqlite3.connect(_DB)


def add_note(text: str) -> str:
    with _conn() as c:
        c.execute("INSERT INTO notes(text, ts) VALUES (?,?)", (text.strip(), time.time()))
    return f"Noted: {text.strip()}"


def list_notes() -> str:
    with _conn() as c:
        rows = c.execute("SELECT id, text FROM notes ORDER BY id DESC LIMIT 20").fetchall()
    if not rows:
        return "No notes yet."
    return "Notes:\n" + "\n".join(f"- [{r[0]}] {r[1]}" for r in rows)


def search_notes(query: str) -> str:
    with _conn() as c:
        rows = c.execute("SELECT id, text FROM notes WHERE text LIKE ? ORDER BY id DESC",
                         (f"%{query}%",)).fetchall()
    if not rows:
        return f"No notes matching '{query}'."
    return "Matches:\n" + "\n".join(f"- [{r[0]}] {r[1]}" for r in rows)


def delete_note(note_id: int) -> str:
    with _conn() as c:
        c.execute("DELETE FROM notes WHERE id=?", (int(note_id),))
    return f"Note {note_id} deleted."
