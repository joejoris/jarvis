#!/bin/sh
# Install JARVIS on Linux or macOS
set -e
cd "$(dirname "$0")/.."

echo "=== JARVIS installer ==="
command -v python3 >/dev/null || { echo "python3 not found — install Python 3.11+ first"; exit 1; }
command -v ollama >/dev/null && echo "✓ ollama found (optional local model)" || echo "… ollama not found (optional; JARVIS works cloud-first via Groq)"

python3 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
if [ ! -f config.yaml ]; then
  cp config.example.yaml config.yaml
  echo "→ created config.yaml from template — add your FREE Groq key: https://console.groq.com/keys"
fi
echo ""
echo "Done. Start JARVIS with:  ./scripts/run.sh"
echo "Then open:                http://localhost:8000/"
