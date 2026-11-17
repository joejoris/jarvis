"""JARVIS FastAPI server: REST + WebSocket, serves the HUD."""
import os
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from backend import config
from backend.memory import store
from backend.brain import llm
from backend.voice import stt, tts, wake, fingerprint
from backend.tools import pc
import asyncio as _asyncio


async def _send_safe(ws, payload):
    try:
        await ws.send_json(payload)
        return True
    except Exception:
        return False

_clients: set = set()
_loop = None


async def broadcast(payload: dict):
    dead = []
    for ws in list(_clients):
        try:
            await ws.send_json(payload)
        except Exception:
            dead.append(ws)
    for d in dead:
        _clients.discard(d)


def _bc(payload: dict):
    if _loop:
        _asyncio.run_coroutine_threadsafe(broadcast(payload), _loop)


_brief_state = {"last_date": None}


def _morning_briefing_due() -> bool:
    cfg = CFG.get("briefing", {})
    if not cfg.get("enabled"):
        return False
    import time as _time
    from datetime import datetime
    t = cfg.get("time", "07:30")
    now = datetime.now().strftime("%H:%M")
    today = datetime.now().date().isoformat()
    return now == t and _brief_state["last_date"] != today


def _reminder_watcher():
    """Fire due reminders: broadcast to HUD, speak aloud, mark done."""
    import time as _time
    seen = set()
    while True:
        try:
            now = _time.time()
            if _morning_briefing_due():
                from datetime import datetime
                from backend.tools import productivity
                _brief_state["last_date"] = datetime.now().date().isoformat()
                text = productivity.briefing()
                _bc({"type": "reminder_fired", "text": "Morning briefing: " + text.splitlines()[0]})
                try:
                    tts.speak(text)
                except Exception:
                    pass
            for r in store.pending_reminders():
                due = r.get("due")
                if due and due <= now and r["id"] not in seen:
                    seen.add(r["id"])
                    print(f'REMINDER FIRED: {r["text"]}', flush=True)
                    store.complete_reminder(r["id"])
                    msg = f"Reminder: {r['text']}"
                    from backend.tools import ironman
                    if not ironman.alerts_muted():
                        _bc({"type": "reminder_fired", "text": r["text"]})
                        try:
                            tts.speak(msg)
                        except Exception:
                            pass
                    else:
                        print(f"Suppressed (going dark): {r['text']}", flush=True)
        except Exception as e:
            print(f"Reminder watcher error: {e}")
        _time.sleep(30)


def _voice_pipeline():
    """Wake → record → transcribe → think (streamed) → speak → broadcast to HUD."""
    try:
        _bc({"type": "status", "value": "listening"})
        pcm = stt.record_until_silence(5.0)
        if fingerprint.gate_enabled() and not fingerprint.verify_wav_bytes(pcm):
            _bc({"type": "error", "text": "Voice not recognized."})
            _bc({"type": "status", "value": "idle"})
            return
        text = stt.transcribe_wav_bytes(pcm)
        _bc({"type": "transcript", "text": text})
        if text:
            _bc({"type": "reply_start"})
            parts = []
            for delta in llm.think_stream(text):
                parts.append(delta)
                _bc({"type": "token", "text": delta})
            reply = "".join(parts).strip()
            _bc({"type": "reply_end", "text": reply})
            if reply:
                tts.speak(reply)
    except Exception as e:
        _bc({"type": "error", "text": f"Voice pipeline failed: {e}"})
    _bc({"type": "status", "value": "idle"})




CFG = config.CONFIG
ROOT = CFG["_root"]
HUD_DIR = os.path.join(ROOT, "hud")

store.init(CFG["_data_dir"])

app = FastAPI(title="JARVIS")


@app.middleware("http")
async def _no_cache_hud(request, call_next):
    response = await call_next(request)
    path = request.url.path
    if path == "/" or path == "/chat" or path.startswith("/hud"):
        response.headers["Cache-Control"] = "no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
    return response


class ChatIn(BaseModel):
    message: str


class ProfileIn(BaseModel):
    name: str


@app.post("/api/profile")
def profile(body: ProfileIn):
    name = (body.name or "").strip()[:60]
    if name:
        store.remember(f"The user's name is {name}")
    return {"ok": True, "name": name}


@app.get("/api/history")
def history(limit: int = 200):
    with store._conn() as c:
        rows = c.execute(
            "SELECT role, content, ts FROM history ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    rows.reverse()
    return {"messages": [{"role": r, "content": c, "ts": t} for r, c, t in rows]}


@app.get("/api/history/export")
def history_export():
    from datetime import datetime
    with store._conn() as c:
        rows = c.execute("SELECT role, content, ts FROM history ORDER BY id").fetchall()
    lines = ["# JARVIS Conversation Export", f"_Exported {datetime.now():%Y-%m-%d %H:%M}_", ""]
    for role, content, ts in rows:
        name = "You" if role == "user" else "JARVIS"
        lines.append(f"### {name} — {datetime.fromtimestamp(ts):%Y-%m-%d %H:%M}")
        lines.append(content)
        lines.append("")
    from fastapi.responses import Response
    return Response(chr(10).join(lines), media_type="text/markdown",
                    headers={"Content-Disposition": 'attachment; filename="jarvis-history.md"'})


@app.get("/api/weather")
def weather():
    from backend.tools import web
    loc = CFG.get("location", {})
    lat, lon, city = loc.get("latitude", 51.5072), loc.get("longitude", -0.1276), loc.get("city", "London")
    return {"text": web.weather(lat, lon, city)}


@app.get("/api/health")
def health():
    return {
        "status": "online",
        "ollama": llm.ollama_available(),
        "voice_stt": stt.available(),
        "wake": wake.available(),
        "model": llm.active_model(),
        "provider": llm.LLM.get("provider", "ollama"),
    }


@app.post("/api/chat")
def chat(body: ChatIn):
    try:
        reply = llm.think(body.message)
        return {"reply": reply}
    except Exception as e:
        return JSONResponse({"error": f"Brain unavailable: {e}. Is 'ollama serve' running and model pulled?"},
                            status_code=503)


@app.get("/api/stats")
def stats():
    try:
        import psutil
        return {"cpu": psutil.cpu_percent(interval=0.3),
                "ram": psutil.virtual_memory().percent,
                "disk": psutil.disk_usage("C:\\").percent}
    except Exception:
        return {"cpu": None, "ram": None, "disk": None}


@app.post("/api/clear_history")
def clear_history():
    with store._conn() as c:
        c.execute("DELETE FROM history")
    return {"cleared": True}




@app.get("/api/facts")
def facts():
    return {"facts": store.all_facts()}


@app.delete("/api/facts")
def delete_facts():
    with store._conn() as c:
        c.execute("DELETE FROM facts")
    return {"cleared": True}


@app.get("/api/reminders")
def reminders():
    return store.pending_reminders()


@app.get("/api/todos")
def todos():
    return store.list_todos()


@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await ws.accept()
    _clients.add(ws)
    try:
        while True:
            try:
                data = await ws.receive_json()
            except Exception:
                break
            kind = data.get("type")
            if kind == "chat":
                if not await _send_safe(ws, {"type": "status", "value": "thinking"}):
                    break
                try:
                    reply_parts = []
                    import queue, threading
                    q = queue.Queue()
                    def worker():
                        try:
                            for delta in llm.think_stream(data.get("text", "")):
                                q.put(("token", delta))
                            q.put(("done", None))
                        except Exception as e:
                            q.put(("error", str(e)))
                    threading.Thread(target=worker, daemon=True).start()
                    if not await _send_safe(ws, {"type": "reply_start"}):
                        break
                    alive = True
                    while alive:
                        tag, payload = await asyncio.to_thread(q.get)
                        if tag == "token":
                            reply_parts.append(payload)
                            alive = await _send_safe(ws, {"type": "token", "text": payload})
                        elif tag == "done":
                            break
                        elif tag == "error":
                            await _send_safe(ws, {"type": "error", "text": payload})
                            alive = False
                    reply = "".join(reply_parts).strip()
                    await _send_safe(ws, {"type": "reply_end", "text": reply})
                    if reply and CFG["voice"].get("enabled"):
                        await asyncio.to_thread(tts.speak, reply)
                except Exception as e:
                    await _send_safe(ws, {"type": "error", "text": str(e)})
                await _send_safe(ws, {"type": "status", "value": "idle"})
            elif kind == "voice":
                if not await _send_safe(ws, {"type": "status", "value": "listening"}):
                    break
                try:
                    pcm = await asyncio.to_thread(stt.record_until_silence, 5.0)
                    if fingerprint.gate_enabled() and not await asyncio.to_thread(fingerprint.verify_wav_bytes, pcm):
                        await _send_safe(ws, {"type": "error", "text": "Voice not recognized."})
                        await _send_safe(ws, {"type": "status", "value": "idle"})
                        continue
                    text = await asyncio.to_thread(stt.transcribe_wav_bytes, pcm)
                    if not await _send_safe(ws, {"type": "transcript", "text": text}):
                        break
                    if text:
                        reply_parts = []
                        for delta in llm.think_stream(text):
                            reply_parts.append(delta)
                            if not await _send_safe(ws, {"type": "token", "text": delta}):
                                break
                        reply = "".join(reply_parts).strip()
                        await _send_safe(ws, {"type": "reply_end", "text": reply})
                        if reply:
                            await asyncio.to_thread(tts.speak, reply)
                except Exception as e:
                    await _send_safe(ws, {"type": "error", "text": f"Voice failed: {e}"})
                await _send_safe(ws, {"type": "status", "value": "idle"})
    except WebSocketDisconnect:
        pass
    finally:
        _clients.discard(ws)


@app.get("/chat")
def chat_page():
    return FileResponse(os.path.join(HUD_DIR, "chat.html"),
                        headers={"Cache-Control": "no-store"})


@app.get("/")
def index():
    return FileResponse(os.path.join(HUD_DIR, "index.html"))


app.mount("/hud", StaticFiles(directory=HUD_DIR), name="hud")


@app.on_event("startup")
async def _startup():
    global _loop
    _loop = _asyncio.get_running_loop()
    import threading
    threading.Thread(target=_reminder_watcher, daemon=True).start()
    if CFG["voice"].get("wake_enabled") and wake.available():
        listener = wake.WakeListener(on_wake=_voice_pipeline)
        threading.Thread(target=listener.run, daemon=True).start()
        print("Wake word listener started ('hey jarvis')")
    else:
        print("Wake word disabled or unavailable")
