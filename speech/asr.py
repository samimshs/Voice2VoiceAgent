"""
Phase 5, Task 5.1 — Automatic Speech Recognition using OpenAI Whisper API.

Takes a path to a WAV/MP3 file and returns the transcribed text.
Uses the cloud API — no model download required.
"""
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def transcribe(audio_file_path: str) -> str:
    """Send an audio file to OpenAI Whisper and return the transcript."""
    if not os.path.exists(audio_file_path):
        raise FileNotFoundError(f"Audio file not found: {audio_file_path}")

    if os.path.getsize(audio_file_path) == 0:
        raise ValueError(f"Audio file is empty: {audio_file_path}")

    with open(audio_file_path, "rb") as f:
        result = _client.audio.transcriptions.create(
            model="whisper-1",
            file=f,
        )

    return result.text.strip()
