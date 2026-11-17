"""Local calendar / agenda tools (SQLite-backed, offline)."""
from datetime import datetime, timedelta
from backend.memory import store


def add_event(title: str, date: str, time: str = "") -> str:
    # Basic sanity: date must parse as YYYY-MM-DD
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        return f"Could not parse date '{date}'. Use YYYY-MM-DD (e.g. 2026-11-20)."
    if time:
        try:
            datetime.strptime(time, "%H:%M")
        except ValueError:
            return f"Could not parse time '{time}'. Use HH:MM (e.g. 14:30)."
    store.add_event(title, date, time)
    label = f"{date} {time}".strip()
    return f"Event added: {title} — {label}."


def list_events(days: int = 7) -> str:
    events = store.list_events(int(days))
    if not events:
        return f"No events in the next {int(days)} days. Your agenda is clear."
    lines = [f"- [{e['id']}] {e['date']} {e['time']} — {e['title']}".replace("  ", " ") for e in events]
    return "Upcoming events:\n" + "\n".join(lines)


def delete_event(event_id: int) -> str:
    store.delete_event(int(event_id))
    return f"Event {event_id} deleted."
