"""JARVIS signature capabilities: suit reports, markets, world clock,
security sweeps, daily digests, countdowns, and going-dark mode."""
import os
import subprocess
import datetime
from backend import config
from backend.memory import store
from backend.tools import web

CFG = config.CONFIG

_going_dark = False


def suit_status() -> str:
    import psutil
    cpu = psutil.cpu_percent(interval=0.4)
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage("C:\\")
    procs = len(psutil.pids())
    boot = datetime.datetime.fromtimestamp(psutil.boot_time()).strftime("%H:%M")
    return (f"Suit diagnostics: reactor efficiency {100 - cpu / 10:.1f}%, "
            f"core temp nominal ({cpu:.0f}% load), shielding {100 - ram.percent:.0f}% integrity. "
            f"Voice link stable, biometrics on standby, {procs} subsystems tracked. "
            f"Uptime since {boot}. Arc reactor output: optimal. All systems nominal, sir.")


def markets() -> str:
    import requests
    out = []
    for sym, name in [("%5EGSPC", "S&P 500"), ("%5EIXIC", "Nasdaq"), ("%5EDJI", "Dow Jones")]:
        try:
            r = requests.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?interval=1d&range=2d",
                             headers={"User-Agent": "Mozilla/5.0"}, timeout=12)
            r.raise_for_status()
            res = r.json()["chart"]["result"][0]
            closes = [c for c in res["indicators"]["quote"][0]["close"] if c is not None]
            if len(closes) >= 2:
                prev, last = closes[-2], closes[-1]
                delta = (last - prev) / prev * 100
                arrow = "▲" if delta >= 0 else "▼"
                out.append(f"{name}: {last:,.2f} ({arrow}{abs(delta):.2f}%)")
            else:
                out.append(f"{name}: {closes[-1]:,.2f}")
        except Exception:
            out.append(f"{name}: unavailable")
    return "Markets: " + " | ".join(out)


_TZ = {
    "london": "Europe/London", "nairobi": "Africa/Nairobi", "tokyo": "Asia/Tokyo",
    "sydney": "Australia/Sydney", "new york": "America/New_York", "los angeles": "America/Los_Angeles",
    "dubai": "Asia/Dubai", "berlin": "Europe/Berlin", "paris": "Europe/Paris",
    "moscow": "Europe/Moscow", "delhi": "Asia/Kolkata", "mumbai": "Asia/Kolkata",
    "singapore": "Asia/Singapore", "hong kong": "Asia/Hong_Kong", "seoul": "Asia/Seoul",
    "toronto": "America/Toronto", "vancouver": "America/Vancouver", "chicago": "America/Chicago",
    "istanbul": "Europe/Istanbul", "cairo": "Africa/Cairo", "lagos": "Africa/Lagos",
    "accra": "Africa/Accra", "lisbon": "Europe/Lisbon", "madrid": "Europe/Madrid",
    "amsterdam": "Europe/Amsterdam", "rome": "Europe/Rome", "athens": "Europe/Athens",
    "jeddah": "Asia/Riyadh", "riyadh": "Asia/Riyadh", "bangkok": "Asia/Bangkok",
    "beijing": "Asia/Shanghai", "shanghai": "Asia/Shanghai", "auckland": "Pacific/Auckland",
}


def world_time(place: str) -> str:
    from zoneinfo import ZoneInfo
    key = place.strip().lower()
    tz = _TZ.get(key) or _TZ.get(key.title().lower())
    try:
        if not tz:
            # try direct IANA guess
            tz = next((v for k, v in _TZ.items() if key in k), None)
        if not tz:
            return f"I don't have '{place}' on file — try London, Nairobi, Tokyo, New York, Sydney…"
        now = datetime.datetime.now(ZoneInfo(tz))
        return f"{place.title()}: {now:%H:%M} on {now:%A, %d %B}."
    except Exception as e:
        return f"World clock failed: {e}"


def security_sweep() -> str:
    out = []
    # Windows Firewall
    try:
        r = subprocess.run(["netsh", "advfirewall", "show", "currentprofile"],
                           capture_output=True, text=True, timeout=20)
        state = "ON" if "ON" in r.stdout.upper() else "UNKNOWN"
        out.append(f"Firewall: {state}")
    except Exception:
        out.append("Firewall: check failed")
    # Windows Defender
    try:
        r = subprocess.run(["powershell", "-NoProfile", "-Command",
                            "(Get-MpComputerStatus).AntivirusEnabled"],
                           capture_output=True, text=True, timeout=25)
        val = r.stdout.strip().lower()
        out.append("Defender AV: " + ("active" if val == "true" else "INACTIVE — investigate"))
    except Exception:
        out.append("Defender AV: check failed")
    # Established connections
    try:
        import psutil
        conns = [c for c in psutil.net_connections(kind="tcp") if c.status == "ESTABLISHED"]
        out.append(f"Open connections: {len(conns)}")
    except Exception:
        out.append("Connections: unavailable")
    # Free disk space as sanity
    try:
        import psutil
        free = psutil.disk_usage("C:\\").free // (2**30)
        out.append(f"Free disk: {free} GB")
    except Exception:
        pass
    return "Security sweep: " + " | ".join(out) + ". Report complete."


def digest() -> str:
    from backend.tools import productivity
    from backend.tools import agenda as _agenda
    day = datetime.datetime.now().strftime("%A, %d %B")
    brief = productivity.briefing()
    agenda_now = _agenda.list_events(3)
    return f"Daily digest — {day}:\n{brief}\n{agenda_now}"


def countdown() -> str:
    events = store.list_events(30)
    if not events:
        return "No upcoming events on the calendar, sir. Cleared schedule."
    e = events[0]
    try:
        when = datetime.datetime.strptime(f"{e['date']} {e['time'] or '00:00'}", "%Y-%m-%d %H:%M")
        delta = when - datetime.datetime.now()
        if delta.total_seconds() < 0:
            return f"{e['title']} has already passed."
        days, rem = divmod(int(delta.total_seconds()), 86400)
        hours, rem = divmod(rem, 3600)
        minutes = rem // 60
        if days:
            return f"{e['title']} is in {days} day{'s' if days > 1 else ''}, {hours} hours ({when:%a %d %b %H:%M})."
        return f"{e['title']} is in {hours} hours and {minutes} minutes ({when:%H:%M})."
    except Exception:
        return f"Next: {e['title']} on {e['date']} {e['time']}."


def go_dark() -> str:
    global _going_dark
    _going_dark = True
    return "Understood. Going dark — all alerts and voice notifications are muted. Say 'coming online' or 'resume' to re-enable."


def come_online() -> str:
    global _going_dark
    _going_dark = False
    return "Back online. All notifications and voice alerts restored."


def alerts_muted() -> bool:
    return _going_dark
