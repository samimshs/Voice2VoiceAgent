"""
Phase 5, Task 5.2 — Fragment-based audio recorder.

Usage:
  from speech.recorder import record_to_file
  path = record_to_file()   # blocks until user presses Enter twice

Press Enter to START recording, press Enter again to STOP.
Audio is saved to temp/recording.wav.
"""
import os
import threading
import sounddevice as sd
import soundfile as sf
import numpy as np

SAMPLE_RATE = 16_000   # Whisper works best at 16 kHz
CHANNELS    = 1        # Mono
OUTPUT_PATH = "temp/recording.wav"


def record_to_file(output_path: str = OUTPUT_PATH) -> str:
    """Record from the microphone until Enter is pressed. Returns the saved file path."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    frames = []
    stop_event = threading.Event()

    def _record():
        with sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS, dtype="float32") as stream:
            while not stop_event.is_set():
                chunk, _ = stream.read(1024)
                frames.append(chunk)

    print("\n🎙  Press Enter to START recording...")
    input()

    thread = threading.Thread(target=_record, daemon=True)
    thread.start()
    print("🔴 Recording... Press Enter to STOP.")

    input()
    stop_event.set()
    thread.join()

    if not frames:
        raise RuntimeError("No audio was captured.")

    audio = np.concatenate(frames, axis=0)
    sf.write(output_path, audio, SAMPLE_RATE)
    duration = len(audio) / SAMPLE_RATE
    print(f"✅ Saved {duration:.1f}s of audio to {output_path}")
    return output_path
