@echo off
title JARVIS Launcher
cd /d "%~dp0.."
start "" /min ollama serve 2>nul
timeout /t 3 /nobreak >nul
start "" /min .venv\Scripts\python.exe -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --ws-ping-interval 120 --ws-ping-timeout 120
timeout /t 5 /nobreak >nul
start http://127.0.0.1:8000/
