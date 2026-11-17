"""Voice enrollment tool: 'enroll my voice'."""
from backend.voice import fingerprint


def enroll_voice() -> str:
    print(fingerprint.enroll())
    return "Voice fingerprint saved. To enable the gate, set voice.fingerprint_gate: true in config.yaml and restart JARVIS."
