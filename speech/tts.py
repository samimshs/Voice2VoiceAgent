"""
Phase 6, Task 6.2 — Text-to-Speech using OpenAI TTS API.

speak()      → converts text to an MP3 file
play_audio() → plays the MP3 using macOS built-in afplay (no extra packages)
"""
import os
import subprocess
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

_client     = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
OUTPUT_PATH = "temp/response.mp3"

# Available voices: alloy, echo, fable, onyx, nova, shimmer
VOICE = "nova"


def speak(text: str, output_path: str = OUTPUT_PATH) -> str:
    """Convert text to speech and save as MP3. Returns the saved file path."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    response = _client.audio.speech.create(
        model="tts-1",
        voice=VOICE,
        input=text,
    )
    response.stream_to_file(output_path)
    return output_path


def play_audio(file_path: str) -> None:
    """Play an audio file using macOS afplay (built-in, no install needed)."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Audio file not found: {file_path}")
    subprocess.run(["afplay", file_path], check=True)
