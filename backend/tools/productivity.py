"""Productivity tools: reminders, todos, remember/recall, datetime."""
import time
from datetime import datetime
from backend.memory import store
from backend.tools import web as _web


def briefing() -> str:
    from datetime import datetime
    parts = [datetime.now().strftime("Good %A, %d %B %Y. It's %H:%M.")]
    try:
        from backend import config
        loc = config.CONFIG.get("location", {})
        parts.append(_web.weather(loc.get("latitude", 51.5072), loc.get("longitude", -0.1276), loc.get("city", "")))
    except Exception:
        pass
    rem = store.pending_reminders()
    parts.append("Reminders: " + (", ".join(r["text"] for r in rem) or "none pending"))
    todos = store.list_todos()
    parts.append("Todos: " + (", ".join(t["text"] for t in todos) or "none"))
    try:
        parts.append(_web.news("", 3))
    except Exception:
        pass
    return "\n".join(parts)


def add_reminder(text: str, minutes_from_now: float | None = None) -> str:
    due = time.time() + minutes_from_now * 60 if minutes_from_now else None
    store.add_reminder(text, due)
    if due:
        return f"Reminder set: {text} in {minutes_from_now:g} minutes."
    return f"Reminder noted: {text}"


def list_reminders() -> str:
    items = store.pending_reminders()
    if not items:
        return "No pending reminders."
    lines = []
    for r in items:
        if r["due"]:
            lines.append(f"- [{r['id']}] {r['text']} (due {datetime.fromtimestamp(r['due']):%Y-%m-%d %H:%M})")
        else:
            lines.append(f"- [{r['id']}] {r['text']}")
    return "Pending reminders:\n" + "\n".join(lines)


def complete_reminder(reminder_id: int) -> str:
    store.complete_reminder(reminder_id)
    return f"Reminder {reminder_id} done."


def add_todo(text: str) -> str:
    store.add_todo(text)
    return f"Added to your list: {text}"


def list_todos() -> str:
    items = store.list_todos()
    if not items:
        return "Your todo list is clear."
    return "Todos:\n" + "\n".join(f"- [{t['id']}] {t['text']}" for t in items)


def complete_todo(todo_id: int) -> str:
    store.complete_todo(todo_id)
    return f"Todo {todo_id} done."


def remember(fact: str) -> str:
    store.remember(fact)
    return f"Noted. I'll remember that {fact}"


def recall() -> str:
    facts = store.all_facts()
    return "Things I remember:\n" + "\n".join(f"- {f}" for f in facts) if facts else "I don't have any long-term memories yet."


def datetime_now() -> str:
    return datetime.now().strftime("It is %A, %d %B %Y, %H:%M.")
