"""Google integration without OAuth pain:

- Calendar: read events from a secret iCal subscription URL
  (Google Calendar → Settings → your calendar → Integrate calendar → Secret address in iCal format)
  config: google.ics_url: "https://calendar.google.com/calendar/ical/…/public/basic.ics"
- Email: IMAP (see email.py)
"""
import datetime
import requests
from backend import config

CFG = config.CONFIG
UA = {"User-Agent": "JARVIS/1.0"}


def google_calendar(days: int = 7) -> str:
    url = (CFG.get("google", {}) or {}).get("ics_url", "").strip()
    if not url:
        return ("Google Calendar is not configured. Paste the 'Secret address in iCal format' "
                "from Google Calendar settings into google.ics_url in config.yaml.")
    try:
        import icalendar
    except ImportError:
        return "icalendar package missing — run: pip install icalendar"
    try:
        r = requests.get(url, headers=UA, timeout=15)
        r.raise_for_status()
        cal = icalendar.Calendar.from_ical(r.content)
        today = datetime.date.today()
        end = today + datetime.timedelta(days=int(days))
        rows = []
        for component in cal.walk():
            if component.name != "VEVENT":
                continue
            start = component.get("DTSTART").dt
            if hasattr(start, "date") and not isinstance(start, datetime.date):
                start_date = start.date()
                when = start.strftime("%Y-%m-%d %H:%M")
            else:
                start_date = start
                when = start_date.isoformat()
            if today <= start_date <= end:
                rows.append((start_date, when, str(component.get("SUMMARY", "(no title)"))))
        rows.sort(key=lambda x: x[0])
        if not rows:
            return f"No Google Calendar events in the next {int(days)} days."
        lines = [f"- {when} — {summary}" for _, when, summary in rows]
        return "Google Calendar (next " + str(int(days)) + " days):\n" + "\n".join(lines)
    except Exception as e:
        return f"Could not read Google Calendar: {e}"
