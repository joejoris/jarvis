"""Speech-to-text. Groq cloud Whisper (fast) by default; local faster-whisper optional."""
import io
import wave
import tempfile
import requests
import numpy as np
from backend import config

CFG = config.CONFIG
_VOICE = CFG.get("voice", {})
_GROQ = CFG.get("llm", {}).get("groq", {})
_model = None


def available() -> bool:
    if _VOICE.get("stt_provider", "groq") == "groq":
        return bool(_GROQ.get("api_key"))
    try:
        import faster_whisper  # noqa
        import sounddevice  # noqa
        return True
    except Exception:
        return False


def _wav_bytes_from_float32(audio: np.ndarray, sample_rate: int = 16000) -> bytes:
    audio = np.nan_to_num(np.clip(audio, -1.0, 1.0), nan=0.0)
    peak = np.max(np.abs(audio)) if audio.size else 0.0
    if peak > 0:
        audio = audio * (0.9 / peak)   # auto-gain: always normalize to strong (Whisper-safe)
    pcm16 = (audio * 32767).astype(np.int16)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sample_rate)
        w.writeframes(pcm16.tobytes())
    return buf.getvalue()


def _groq_transcribe(wav_bytes: bytes) -> str:
    r = requests.post(
        f"{_GROQ['base_url']}/audio/transcriptions",
        headers={"Authorization": f"Bearer {_GROQ['api_key']}"},
        files={"file": ("audio.wav", wav_bytes, "audio/wav")},
        data={"model": "whisper-large-v3-turbo", "response_format": "json"},
        timeout=60)
    r.raise_for_status()
    return (r.json().get("text") or "").strip()


def _load_local():
    global _model
    if _model is None:
        from faster_whisper import WhisperModel
        _model = WhisperModel(_VOICE.get("stt_model", "tiny"), device="cpu", compute_type="int8")
    return _model


def transcribe_wav_bytes(wav_bytes: bytes) -> str:
    if _VOICE.get("stt_provider", "groq") == "groq":
        try:
            return _groq_transcribe(wav_bytes)
        except Exception as e:
            print(f"Groq STT failed ({e}); falling back to local whisper")
    import soundfile as sf
    model = _load_local()
    data, sr = sf.read(io.BytesIO(wav_bytes))
    if data.ndim > 1:
        data = data.mean(axis=1)
    segments, _ = model.transcribe(data, beam_size=1)
    return " ".join(s.text for s in segments).strip()


def _rms(block: np.ndarray) -> float:
    if block.size == 0:
        return 0.0
    return float(np.sqrt(np.mean(np.square(block, dtype=np.float64))))


def record_until_silence(max_seconds: float = 10.0, silence_after: float = 1.3,
                         sample_rate: int = 16000) -> bytes:
    """Record with end-of-speech detection: stops after ~1.3s of silence post-speech.
    Falls back to fixed capture if no speech is detected in the window."""
    import sounddevice as sd
    blocksize = 480  # 30 ms at 16 kHz
    frames: list[np.ndarray] = []
    print(f"Listening… (max {max_seconds}s)")
    stream = sd.InputStream(samplerate=sample_rate, channels=1, dtype="float32",
                            blocksize=blocksize)
    stream.start()
    try:
        # adaptive noise floor from first 0.5s
        floor_blocks = []
        for _ in range(int(0.5 / 0.03)):
            block, _ = stream.read(blocksize)
            floor_blocks.append(block.flatten())
        noise = max(0.002, np.percentile([_rms(b) for b in floor_blocks], 90) * 2.5)
        speech_started = False
        elapsed = 0.5
        silence_run = 0.0
        captured = list(floor_blocks)
        while elapsed < max_seconds:
            block, _ = stream.read(blocksize)
            block = block.flatten()
            captured.append(block)
            level = _rms(block)
            elapsed += 0.03
            if level > noise:
                speech_started = True
                silence_run = 0.0
            elif speech_started:
                silence_run += 0.03
                if silence_run >= silence_after:
                    break
        if not speech_started:
            print("No speech detected — using the captured audio anyway.")
        audio = np.concatenate(captured)
    finally:
        stream.stop()
        stream.close()
    return _wav_bytes_from_float32(audio, sample_rate)


def transcribe_bytes(pcm_bytes: bytes, sample_rate: int = 16000) -> str:
    """Backward-compatible: float32 PCM bytes → wav → transcript."""
    audio = np.frombuffer(pcm_bytes, dtype=np.float32)
    return transcribe_wav_bytes(_wav_bytes_from_float32(audio, sample_rate))
