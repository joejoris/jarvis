"""Tool registry: JSON schemas for Ollama function calling + dispatcher."""
from backend.tools import pc, web, productivity, homeassistant, agenda, email, notes, translate, google_calendar, spotify, webcam, voicegate, ironman
from backend import config

CFG = config.CONFIG
LOC = CFG.get("location", {"latitude": 51.5072, "longitude": -0.1276, "city": "London"})

TOOLS = [
    {"type": "function", "function": {"name": "open_app", "description": "Open an application on the PC",
        "parameters": {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]}}},
    {"type": "function", "function": {"name": "set_volume", "description": "Adjust PC volume",
        "parameters": {"type": "object", "properties": {"action": {"type": "string", "enum": ["up", "down", "mute"]}}, "required": ["action"]}}},
    {"type": "function", "function": {"name": "system_power", "description": "Shutdown, restart or log off the PC. Requires user confirmation.",
        "parameters": {"type": "object", "properties": {"action": {"type": "string", "enum": ["shutdown", "restart", "logoff"]}, "confirmed": {"type": "boolean"}}, "required": ["action"]}}},
    {"type": "function", "function": {"name": "system_stats", "description": "Get CPU and RAM usage",
        "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "screenshot", "description": "Take a screenshot",
        "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "web_search", "description": "Search the live web via Bing RSS",
        "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}},
    {"type": "function", "function": {"name": "weather", "description": "Get current weather and today's forecast",
        "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "news", "description": "Get live news headlines. Optionally pass a topic to search Google News for current coverage.",
        "parameters": {"type": "object", "properties": {"topic": {"type": "string"}}}}},
    {"type": "function", "function": {"name": "add_reminder", "description": "Set a reminder",
        "parameters": {"type": "object", "properties": {"text": {"type": "string"}, "minutes_from_now": {"type": "number"}}, "required": ["text"]}}},
    {"type": "function", "function": {"name": "list_reminders", "description": "List pending reminders",
        "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "complete_reminder", "description": "Mark a reminder done",
        "parameters": {"type": "object", "properties": {"reminder_id": {"type": "integer"}}, "required": ["reminder_id"]}}},
    {"type": "function", "function": {"name": "add_todo", "description": "Add an item to the todo list",
        "parameters": {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}}},
    {"type": "function", "function": {"name": "list_todos", "description": "List pending todos",
        "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "complete_todo", "description": "Mark a todo done",
        "parameters": {"type": "object", "properties": {"todo_id": {"type": "integer"}}, "required": ["todo_id"]}}},
    {"type": "function", "function": {"name": "remember", "description": "Store a long-term fact about the user",
        "parameters": {"type": "object", "properties": {"fact": {"type": "string"}}, "required": ["fact"]}}},
    {"type": "function", "function": {"name": "recall", "description": "List all remembered long-term facts",
        "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "ha_turn_on", "description": "Turn on a Home Assistant device, e.g. light.kitchen",
        "parameters": {"type": "object", "properties": {"entity_id": {"type": "string"}}, "required": ["entity_id"]}}},
    {"type": "function", "function": {"name": "ha_turn_off", "description": "Turn off a Home Assistant device, e.g. light.kitchen",
        "parameters": {"type": "object", "properties": {"entity_id": {"type": "string"}}, "required": ["entity_id"]}}},
    {"type": "function", "function": {"name": "ha_get_state", "description": "Get the state of a Home Assistant entity",
        "parameters": {"type": "object", "properties": {"entity_id": {"type": "string"}}, "required": ["entity_id"]}}},
    {"type": "function", "function": {"name": "briefing", "description": "Morning/daily briefing: date, weather, reminders, todos, top headlines. Use when the user asks for a briefing or 'what's my day'.",
        "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "add_event", "description": "Add an event to the local calendar",
        "parameters": {"type": "object", "properties": {"title": {"type": "string"}, "date": {"type": "string", "description": "YYYY-MM-DD"}, "time": {"type": "string", "description": "HH:MM 24h, optional"}}, "required": ["title", "date"]}}},
    {"type": "function", "function": {"name": "list_events", "description": "List upcoming calendar events / agenda",
        "parameters": {"type": "object", "properties": {"days": {"type": "integer", "description": "Days ahead, default 7"}}}}},
    {"type": "function", "function": {"name": "delete_event", "description": "Delete a calendar event by id",
        "parameters": {"type": "object", "properties": {"event_id": {"type": "integer"}}, "required": ["event_id"]}}},
    {"type": "function", "function": {"name": "check_email", "description": "Check unread emails (IMAP)",
        "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "media_control", "description": "Control media playback",
        "parameters": {"type": "object", "properties": {"action": {"type": "string", "enum": ["playpause", "next", "previous", "stop"]}}, "required": ["action"]}}},
    {"type": "function", "function": {"name": "youtube_play", "description": "Open YouTube and search for a video/song",
        "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}},
    {"type": "function", "function": {"name": "add_note", "description": "Save a quick note",
        "parameters": {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}}},
    {"type": "function", "function": {"name": "list_notes", "description": "List recent notes",
        "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "search_notes", "description": "Search notes by keyword",
        "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}},
    {"type": "function", "function": {"name": "delete_note", "description": "Delete a note by id",
        "parameters": {"type": "object", "properties": {"note_id": {"type": "integer"}}, "required": ["note_id"]}}},
    {"type": "function", "function": {"name": "translate", "description": "Translate text between languages",
        "parameters": {"type": "object", "properties": {"text": {"type": "string"}, "target_lang": {"type": "string"}, "source_lang": {"type": "string"}}, "required": ["text", "target_lang"]}}},
    {"type": "function", "function": {"name": "google_calendar", "description": "Read upcoming events from the user's Google Calendar (iCal)",
        "parameters": {"type": "object", "properties": {"days": {"type": "integer"}}}}},
    {"type": "function", "function": {"name": "spotify_play", "description": "Open Spotify and play/search music",
        "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}},
    {"type": "function", "function": {"name": "webcam_see", "description": "Look through the webcam and describe what you see",
        "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "enroll_voice", "description": "Enroll the owner's voice for the voice lock",
        "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "suit_status", "description": "Suit/system diagnostic report with reactor status",
        "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "markets", "description": "Live stock market report: S&P 500, Nasdaq, Dow Jones",
        "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "world_time", "description": "Current time in a city worldwide",
        "parameters": {"type": "object", "properties": {"place": {"type": "string"}}, "required": ["place"]}}},
    {"type": "function", "function": {"name": "security_sweep", "description": "Windows security diagnostic: firewall, Defender, open connections",
        "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "digest", "description": "Daily digest: weather, reminders, todos, agenda, headlines",
        "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "countdown", "description": "Live countdown to the next calendar event",
        "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "go_dark", "description": "Mute all audio and visual alerts ('going dark')",
        "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "come_online", "description": "Re-enable alerts after going dark",
        "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "datetime_now", "description": "Get the current date and time",
        "parameters": {"type": "object", "properties": {}}}},
]


def dispatch(name: str, args: dict) -> str:
    args = args or {}
    try:
        if name == "open_app": return pc.open_app(args["name"])
        if name == "set_volume": return pc.set_volume(args["action"])
        if name == "system_power": return pc.system_power(args["action"], bool(args.get("confirmed", False)))
        if name == "system_stats": return pc.system_stats()
        if name == "screenshot": return pc.screenshot()
        if name == "web_search": return web.web_search(args["query"])
        if name == "weather": return web.weather(LOC["latitude"], LOC["longitude"], LOC.get("city", ""))
        if name == "news": return web.news(args.get("topic", ""))
        if name == "add_reminder": return productivity.add_reminder(args["text"], args.get("minutes_from_now"))
        if name == "list_reminders": return productivity.list_reminders()
        if name == "complete_reminder": return productivity.complete_reminder(int(args["reminder_id"]))
        if name == "add_todo": return productivity.add_todo(args["text"])
        if name == "list_todos": return productivity.list_todos()
        if name == "complete_todo": return productivity.complete_todo(int(args["todo_id"]))
        if name == "remember": return productivity.remember(args["fact"])
        if name == "recall": return productivity.recall()
        if name == "ha_turn_on": return homeassistant.ha_turn_on(args["entity_id"])
        if name == "ha_turn_off": return homeassistant.ha_turn_off(args["entity_id"])
        if name == "ha_get_state": return homeassistant.ha_get_state(args["entity_id"])
        if name == "briefing": return productivity.briefing()
        if name == "add_event": return agenda.add_event(args["title"], args["date"], args.get("time", ""))
        if name == "list_events": return agenda.list_events(args.get("days", 7))
        if name == "delete_event": return agenda.delete_event(int(args["event_id"]))
        if name == "check_email": return email.check_email()
        if name == "media_control": return pc.media_control(args["action"])
        if name == "youtube_play": return pc.youtube_play(args["query"])
        if name == "add_note": return notes.add_note(args["text"])
        if name == "list_notes": return notes.list_notes()
        if name == "search_notes": return notes.search_notes(args["query"])
        if name == "delete_note": return notes.delete_note(int(args["note_id"]))
        if name == "translate": return translate.translate(args["text"], args["target_lang"], args.get("source_lang", "auto"))
        if name == "google_calendar": return google_calendar.google_calendar(args.get("days", 7))
        if name == "spotify_play": return spotify.spotify_play(args["query"])
        if name == "webcam_see": return webcam.webcam_see()
        if name == "enroll_voice": return voicegate.enroll_voice()
        if name == "suit_status": return ironman.suit_status()
        if name == "markets": return ironman.markets()
        if name == "world_time": return ironman.world_time(args["place"])
        if name == "security_sweep": return ironman.security_sweep()
        if name == "digest": return ironman.digest()
        if name == "countdown": return ironman.countdown()
        if name == "go_dark": return ironman.go_dark()
        if name == "come_online": return ironman.come_online()
        if name == "datetime_now": return productivity.datetime_now()
        return f"Unknown tool: {name}"
    except Exception as e:
        return f"Tool {name} failed: {e}"
