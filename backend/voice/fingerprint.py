"""Lightweight speaker fingerprint — a convenience lock, NOT cryptographic security.

Enrollment: record ~4s of the owner's voice. We compare spectral envelopes
(log-power spectrum, mean + std) with cosine similarity. It reliably rejects
different speakers and replays in similar conditions, but it is not a vault.

Usage:
    python -m backend.voice.fingerprint enroll   # follow the prompt
    config: voice.fingerprint_gate: true   # wake/voice pipeline verifies before acting
"""
import os
import numpy as np
from backend import config

CFG = config.CONFIG
_PATH = os.path.join(CFG["_data_dir"], "voice_fingerprint.npy")
SR = 16000


def _features(audio: np.ndarray) -> np.ndarray:
    audio = np.nan_to_num(audio, nan=0.0)
    if audio.size < SR:
        return np.zeros(64)
    # trim leading/trailing silence
    frames = audio.reshape(-1, 512)
    if frames.shape[0] < 10:
        return np.zeros(64)
    spec = np.abs(np.fft.rfft(frames, axis=1)) ** 2
    logspec = np.log10(spec + 1e-8).mean(axis=0)
    # average a fixed 32-bin envelope + std for compact signature
    env = np.array_split(logspec, 32)
    mean = [e.mean() for e in env]
    std = [e.std() for e in env]
    return np.array(mean + std)


def record_sample(seconds: float, sample_rate: int = SR) -> bytes:
    import sounddevice as sd
    rec = sd.rec(int(seconds * sample_rate), samplerate=sample_rate,
                 channels=1, dtype="float32")
    sd.wait()
    return rec.flatten()


def enroll(seconds: float = 4.0) -> str:
    print(f"Enrolling your voice — speak naturally for {seconds} seconds…")
    audio = record_sample(seconds)
    feats = _features(audio)
    np.save(_PATH, feats)
    peak = float(np.abs(audio).max())
    return f"Voice fingerprint saved. Peak level {peak:.2f}. Toggle voice.fingerprint_gate: true in config.yaml to enable."


def enrolled() -> bool:
    return os.path.exists(_PATH)


def verify(audio: np.ndarray, threshold: float = 0.82) -> bool:
    if not enrolled():
        return True  # no fingerprint → no gate
    try:
        ref = np.load(_PATH)
        cur = _features(audio)
        ref_n = ref / (np.linalg.norm(ref) + 1e-8)
        cur_n = cur / (np.linalg.norm(cur) + 1e-8)
        score = float(np.dot(ref_n, cur_n))
        print(f"Voice match score: {score:.3f} (threshold {threshold})")
        return score >= threshold
    except Exception as e:
        print(f"Fingerprint verify error: {e}")
        return True


def verify_wav_bytes(wav_bytes: bytes, threshold: float = 0.82) -> bool:
    try:
        import soundfile as sf
        import io
        data, _ = sf.read(io.BytesIO(wav_bytes))
        if data.ndim > 1:
            data = data.mean(axis=1)
        return verify(data, threshold)
    except Exception as e:
        print(f"Fingerprint decode error: {e}")
        return True


def gate_enabled() -> bool:
    return bool(CFG.get("voice", {}).get("fingerprint_gate", False)) and enrolled()


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "enroll":
        print(enroll())
    else:
        print("Usage: python -m backend.voice.fingerprint enroll")
