"""Webcam vision: capture a frame and ask Gemini to describe it.
Requires a free Google AI Studio key in vision.gemini_api_key."""
import os
import requests
import base64
import tempfile
from backend import config

CFG = config.CONFIG


def _capture_jpeg() -> str | None:
    try:
        import cv2
    except ImportError:
        return None
    cam = cv2.VideoCapture(0)
    if not cam.isOpened():
        return None
    ret, frame = cam.read()
    cam.release()
    if not ret:
        return None
    path = os.path.join(tempfile.gettempdir(), "jarvis_webcam.jpg")
    cv2.imwrite(path, frame)
    return path


def webcam_see() -> str:
    path = _capture_jpeg()
    if not path:
        return "Could not open the webcam (or opencv not installed)."
    vision = CFG.get("vision", {}) or {}
    key = vision.get("gemini_api_key", "").strip()
    if not key:
        return (f"I captured a frame to {path}, but vision needs a key. "
                f"Get a free Gemini API key at https://aistudio.google.com/apikey "
                f"and set vision.gemini_api_key in config.yaml.")
    model = vision.get("gemini_model", "gemini-2.0-flash")
    with open(path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode("ascii")
    try:
        r = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
            f"?key={key}",
            json={"contents": [{"parts": [
                {"text": "Describe what you see in 2 short sentences, in a calm JARVIS voice."},
                {"inline_data": {"mime_type": "image/jpeg", "data": img_b64}},
            ]}]},
            timeout=30)
        r.raise_for_status()
        parts = r.json()["candidates"][0]["content"]["parts"]
        text = "".join(p.get("text", "") for p in parts).strip()
        return f"What I see: {text}"
    except Exception as e:
        return f"Vision request failed: {e}"
