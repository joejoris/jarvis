#!/bin/sh
cd "$(dirname "$0")/.."
if command -v ollama >/dev/null && ! pgrep -x ollama >/dev/null 2>&1; then
  (ollama serve >/dev/null 2>&1 &)
  sleep 2
fi
. .venv/bin/activate
exec uvicorn backend.main:app --host 0.0.0.0 --port 8000 --ws-ping-interval 120 --ws-ping-timeout 120
