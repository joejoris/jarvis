# J.A.R.V.I.S.

**Just A Rather Very Intelligent System** — your Iron Man AI assistant, running free and open-source on your own hardware.

![status](https://img.shields.io/badge/status-working-brightgreen) ![license](https://img.shields.io/badge/license-MIT-blue) ![python](https://img.shields.io/badge/python-3.11%2B-blue)

### ⬇ [Download the latest release — Windows / Linux / macOS](https://github.com/joejoris/jarvis/releases/latest)

## Features

- 🧠 **Fast brain** — Groq cloud inference (`gpt-oss-20b`) or fully-local Ollama (`qwen2.5`)
- 🎙 **Voice in & out** — Groq Whisper STT, optional local faster-whisper fallback, always-on "Hey Jarvis" wake word
- ⚡ **Iron-Man HUD** — arc-reactor interface with boot sequence, suit-skin switcher, red alert mode, voice-reactive core
- 🤖 **44 tools** — weather, live news, markets, web search, reminders, todos, local calendar, email (IMAP), notes, timers, daily briefing, security sweep, translator, Spotify
- 🗣 **Daily spoken briefing** — weather, agenda, todos, headlines, delivered aloud
- 🧠 **Long-term memory** — JARVIS remembers you and what you tell it
- 🔔 **Reminders that actually fire** — spoken aloud + toast + red-alert mode
- 🎛 **Real-time query answering** — live web search, Bing RSS and Google News

## ⬇ Download

| Platform | File | Link |
|----------|------|------|
| 🪟 Windows | `jarvis-windows.zip` | **[Download ⬇](https://github.com/joejoris/jarvis/releases/download/v1.0.0/jarvis-windows.zip)** |
| 🐧 Linux | `jarvis-linux.tar.gz` | **[Download ⬇](https://github.com/joejoris/jarvis/releases/download/v1.0.0/jarvis-linux.tar.gz)** |
| 🍎 macOS | `jarvis-macos.tar.gz` | **[Download ⬇](https://github.com/joejoris/jarvis/releases/download/v1.0.0/jarvis-macos.tar.gz)** |

> All releases: https://github.com/joejoris/jarvis/releases

## Quick start

You need **Python 3.11+**. A **free Groq API key** unlocks the full lightning-fast experience (https://console.groq.com/keys — or use Ollama locally instead).

### Windows
```powershell
git clone https://github.com/joejoris/jarvis.git
cd jarvis
.\scripts\setup.ps1
# edit config.yaml → paste your Groq key
.\scripts\run.ps1
```
Double-click `JARVIS.bat` (created on your Desktop by `setup.ps1`) — or point your browser at **http://localhost:8000/**

### Linux / macOS
```bash
git clone https://github.com/joejoris/jarvis.git
cd jarvis
./scripts/install.sh
# edit config.yaml → paste your Groq key
./scripts/run.sh
```

Open **http://localhost:8000/**

### First-run checklist
1. Paste your free Groq API key into `config.yaml` → `llm.groq.api_key`
2. Set your city in `config.yaml` → `location.latitude/longitude/city`
3. Say **"Hey Jarvis"** or press the mic — voice works out of the box
4. Optional: `google.ics_url` (calendar), `email.*` (Gmail via App Password), `homeassistant.*` (smart home), `vision.gemini_api_key` (webcam vision)

## Architecture

```
HUD (browser/PWA)  ◄──WebSocket──►  FastAPI server ──► Groq API (fast) / Ollama (local)
 voice, camera                         │                    tools: 44 real-time functions
 boot sequence, skins                  ▼                    memory + reminders via SQLite
                                  SQLite memory
```

## Screenshots

Everything runs at `http://localhost:8000/` — the Iron-Man HUD (`/`) and the Claude-style chat (`/chat`).

## License

MIT — see [LICENSE](LICENSE).

Built by [joejoris](https://github.com/joejoris) — a personal AI built from zero, for fun and productivity.
