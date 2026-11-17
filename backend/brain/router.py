"""Keyword-based intent router: tiny models can't handle 17 tool schemas.

Matches the user's text against common intents and dispatches tools directly,
then lets the LLM phrase the result conversationally (short prompt = fast).
Set llm.tool_mode: llm in config.yaml to force LLM function-calling instead.
"""
import re
from backend.tools import dispatch

_RULES = [
    (r"\bweather\b|temperature|forecast|rain", lambda m: ("weather", {})),
    (r"suit up|suit status|diagnostic|diagnostics|run diagnostic|power report|system status report", lambda m: ("suit_status", {})),
    (r"markets?|stock market|dow|nasdaq|s&p", lambda m: ("markets", {})),
    (r"what time is it in ([a-z]+)|time in ([a-z]+)", lambda m: ("world_time", {"place": (m.group(1) or m.group(2)).strip()})),
    (r"security sweep|threat scan|vulnerability scan|sweep", lambda m: ("security_sweep", {})),
    (r"digest|summari[sz]e my day|recap|summari[sz]e the day", lambda m: ("digest", {})),
    (r"countdown|how long until|how long before", lambda m: ("countdown", {})),
    (r"going dark|go dark|mute everything|silent mode", lambda m: ("go_dark", {})),
    (r"coming online|come online|unmute|resume alerts", lambda m: ("come_online", {})),
    (r"play (?:me )?(?!.*spotify)(.+)|put on (?!.*spotify)(.+)", lambda m: ("youtube_play", {"query": (m.group(1) or m.group(2)).strip()})),
    (r"agenda|calendar|my events|what.?s on|what do i have", lambda m: ("list_events", {"days": 7})),
    (r"note that (.+)|take a note[: ]+|remember this note[: ]*", lambda m: ("add_note", {"text": m.group(1).strip() if m.group(1) else m.string})),
    (r"my notes|show (?:my )?notes|list notes", lambda m: ("list_notes", {})),
    (r"translate (.+) to (\w+)", lambda m: ("translate", {"text": m.group(1).strip(), "target_lang": m.group(2).strip()})),
    (r"what.?s on my (?:google )?calendar|check my (?:google )?calendar", lambda m: ("google_calendar", {"days": 7})),
    (r"play (.+) on spotify|spotify (.+)", lambda m: ("spotify_play", {"query": (m.group(1) or m.group(2)).strip()})),
    (r"what do you see|look at (?:this|me|the)", lambda m: ("webcam_see", {})),
    (r"enroll my voice|voice lock|set up voice", lambda m: ("enroll_voice", {})),
    (r"email|inbox|unread|my mail", lambda m: ("check_email", {})),
    (r"playpause|pause|resume|next (?:song|track)|previous (?:song|track)", lambda m: ("media_control", {"action": "playpause"})),
    (r"brief|what.?s my day|morning report|daily update", lambda m: ("briefing", {})),
    (r"\btime\b|\bclock\b|datetime|what day", lambda m: ("datetime_now", {})),
    (r"\bnews\b|headlines", lambda m: ("news", {})),
    (r"\bsystem stats\b|\bcpu\b|\bmemory usage\b|how is the pc", lambda m: ("system_stats", {})),
    (r"\bscreenshot\b|screen ?shot", lambda m: ("screenshot", {})),
    (r"\bopen ([\w .-]+)", lambda m: ("open_app", {"name": m.group(1).strip()})),
    (r"(?:set )?volume (up|down|mute)|turn .*(up|down).*(volume|sound)|unmute",
     lambda m: ("set_volume", {"action": "up" if (m.group(1) or '') == "up" else ("down" if (m.group(1) or '') == "down" else "mute")})),
    (r"\bremember (?:that )?(.+)", lambda m: ("remember", {"fact": m.group(1).strip()})),
    (r"what do you remember|recall", lambda m: ("recall", {})),
    (r"add (?:a )?todo[: ]+(.+)|add (.+) to (?:my )?(?:todo|list)",
     lambda m: ("add_todo", {"text": (m.group(1) or m.group(2)).strip()})),
    (r"(?:list|show|what are) .*todos?|my (?:todo )?list", lambda m: ("list_todos", {})),
    (r"add (?:a )?reminder[: ]+(.+)|remind me (?:to )?(.+)",
     lambda m: ("add_reminder", {"text": (m.group(1) or m.group(2)).strip()})),
    (r"(?:list|show|what are) .*reminders?", lambda m: ("list_reminders", {})),
    (r"search (?:the web )?(?:for )?(.+)|look up (.+)|google (.+)",
     lambda m: ("web_search", {"query": (m.group(1) or m.group(2) or m.group(3)).strip()})),
    (r"turn on ([\w.]+)|switch on ([\w.]+)", lambda m: ("ha_turn_on", {"entity_id": (m.group(1) or m.group(2)).strip()})),
    (r"turn off ([\w.]+)|switch off ([\w.]+)", lambda m: ("ha_turn_off", {"entity_id": (m.group(1) or m.group(2)).strip()})),
    (r"state of ([\w.]+)|is ([\w.]+) (on|off)",
     lambda m: ("ha_get_state", {"entity_id": (m.group(1) or m.group(2)).strip()})),
    (r"shut ?down", lambda m: ("system_power", {"action": "shutdown"})),
    (r"restart( the)? (pc|computer)|reboot", lambda m: ("system_power", {"action": "restart"})),
]
_COMPILED = [(re.compile(p, re.I), fn) for p, fn in _RULES]


def match(text: str):
    """Return (tool_name, args) or None."""
    for rx, fn in _COMPILED:
        m = rx.search(text)
        if m:
            try:
                return fn(m)
            except Exception:
                continue
    return None
