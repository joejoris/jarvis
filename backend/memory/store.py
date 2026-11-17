"""SQLite-backed memory: conversation history + long-term facts + reminders/todos."""
import sqlite3
import time
import os

_DB = None


def init(data_dir: str):
    global _DB
    _DB = os.path.join(data_dir, "jarvis.db")
    with _conn() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS history(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            ts REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS events(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL DEFAULT '',
            ts REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS facts(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fact TEXT NOT NULL UNIQUE,
            ts REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS reminders(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            due REAL,
            done INTEGER DEFAULT 0,
            ts REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS todos(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            done INTEGER DEFAULT 0,
            ts REAL NOT NULL
        );
        """)


def _conn():
    return sqlite3.connect(_DB)


def add_message(role: str, content: str):
    with _conn() as c:
        c.execute("INSERT INTO history(role, content, ts) VALUES (?,?,?)",
                  (role, content, time.time()))


def recent_history(limit: int = 20):
    with _conn() as c:
        rows = c.execute(
            "SELECT role, content FROM history ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    return [{"role": r, "content": c} for r, c in reversed(rows)]


def remember(fact: str):
    with _conn() as c:
        c.execute("INSERT OR IGNORE INTO facts(fact, ts) VALUES (?,?)", (fact, time.time()))


def all_facts():
    with _conn() as c:
        return [r[0] for r in c.execute("SELECT fact FROM facts ORDER BY id")]


def add_reminder(text: str, due: float | None = None):
    with _conn() as c:
        c.execute("INSERT INTO reminders(text, due, ts) VALUES (?,?,?)",
                  (text, due, time.time()))


def pending_reminders():
    with _conn() as c:
        return [{"id": r[0], "text": r[1], "due": r[2]} for r in c.execute(
            "SELECT id, text, due FROM reminders WHERE done=0 ORDER BY due")]


def complete_reminder(rid: int):
    with _conn() as c:
        c.execute("UPDATE reminders SET done=1 WHERE id=?", (rid,))


def add_event(title: str, date: str, time_str: str = ""):
    import time as _time
    with _conn() as c:
        c.execute("INSERT INTO events(title, date, time, ts) VALUES (?,?,?,?)",
                  (title, date, time_str, _time.time()))


def list_events(days_ahead: int = 7):
    from datetime import datetime, timedelta
    today = datetime.now().date()
    end = today + timedelta(days=days_ahead)
    with _conn() as c:
        rows = c.execute(
            "SELECT id, title, date, time FROM events WHERE date >= ? AND date <= ? ORDER BY date, time",
            (today.isoformat(), end.isoformat())).fetchall()
    return [{"id": r[0], "title": r[1], "date": r[2], "time": r[3]} for r in rows]


def delete_event(eid: int):
    with _conn() as c:
        c.execute("DELETE FROM events WHERE id=?", (eid,))


def add_todo(text: str):
    with _conn() as c:
        c.execute("INSERT INTO todos(text, ts) VALUES (?,?)", (text, time.time()))


def list_todos():
    with _conn() as c:
        return [{"id": r[0], "text": r[1]} for r in c.execute(
            "SELECT id, text FROM todos WHERE done=0 ORDER BY id")]


def complete_todo(tid: int):
    with _conn() as c:
        c.execute("UPDATE todos SET done=1 WHERE id=?", (tid,))
