"""Text-to-speech. pyttsx3 (instant, local) by default; Groq Orpheus optional."""
import os
import tempfile
import requests
import soundfile as sf
import sounddevice as sd
from backend import config

CFG = config.CONFIG
_VOICE = CFG.get("voice", {})
_GROQ = CFG.get("llm", {}).get("groq", {})
_engine = None


def _pyttsx3():
    global _engine
    if _engine is None:
        import pyttsx3
        _engine = pyttsx3.init()
        idx = _VOICE.get("tts_voice_index", 0)
        voices = _engine.getProperty("voices") or []
        if voices and 0 <= idx < len(voices):
            _engine.setProperty("voice", voices[idx].id)
        _engine.setProperty("rate", 175)
    return _engine


def _groq_synthesize_to_file(text: str) -> str | None:
    try:
        path = os.path.join(tempfile.gettempdir(), "jarvis_tts.wav")
        r = requests.post(
            f"{_GROQ['base_url']}/audio/speech",
            headers={"Authorization": f"Bearer {_GROQ['api_key']}"},
            json={"model": "canopylabs/orpheus-v1-english",
                  "input": text,
                  "voice": _VOICE.get("tts_groq_voice", "autumn"),
                  "response_format": "wav"},
            timeout=60)
        if r.status_code != 200:
            print(f"Groq TTS {r.status_code}: {r.text[:200]}")
            return None
        with open(path, "wb") as f:
            f.write(r.content)
        return path
    except Exception as e:
        print(f"Groq TTS error: {e}")
        return None


def synthesize_to_file(text: str) -> str | None:
    if _VOICE.get("tts_provider", "pyttsx3") == "groq":
        p = _groq_synthesize_to_file(text)
        if p:
            return p
        print("Falling back to local TTS")
    try:
        path = os.path.join(tempfile.gettempdir(), "jarvis_tts.wav")
        eng = _pyttsx3()
        eng.save_to_file(text, path)
        eng.runAndWait()
        return path
    except Exception:
        return None


def speak(text: str):
    if _VOICE.get("tts_provider", "pyttsx3") == "groq":
        p = _groq_synthesize_to_file(text)
        if p:
            try:
                data, sr = sf.read(p)
                sd.play(data, sr)
                sd.wait()
                return
            except Exception as e:
                print(f"Playback failed ({e}), falling back to local TTS")
    try:
        _pyttsx3().say(text)
        _pyttsx3().runAndWait()
    except Exception:
        pass
