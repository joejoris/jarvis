"""Wake word detection via openWakeWord (pretrained 'hey_jarvis' model).

Runs a blocking capture loop; call from a background thread.
"""
import time
import numpy as np
from backend import config

CFG = config.CONFIG
SAMPLE_RATE = 16000
_CHUNK = 1280  # 80 ms


def available() -> bool:
    try:
        import openwakeword  # noqa
        import sounddevice  # noqa
        return True
    except Exception:
        return False


class WakeListener:
    def __init__(self, on_wake):
        self.on_wake = on_wake
        self._stop = False

    def stop(self):
        self._stop = True

    def run(self):
        import sounddevice as sd
        from openwakeword.model import Model
        try:
            model = Model(wakeword_models=["hey_jarvis"], inference_framework="onnx")
        except Exception:
            import openwakeword.utils as u
            u.download_models(["hey_jarvis"])
            model = Model(wakeword_models=["hey_jarvis"], inference_framework="onnx")
        last_trigger = 0.0
        with sd.InputStream(samplerate=SAMPLE_RATE, channels=1,
                            dtype=np.int16, blocksize=_CHUNK) as stream:
            while not self._stop:
                chunk, _ = stream.read(_CHUNK)
                audio = chunk.flatten()
                prediction = model.predict(audio)
                score = prediction.get("hey_jarvis", 0.0)
                if score > 0.5 and time.time() - last_trigger > 3:
                    last_trigger = time.time()
                    try:
                        self.on_wake()
                    except Exception:
                        pass
