"""
Phase 5 — Test: record → transcribe → run through LangGraph.
Run from the project root:  python scripts/test_asr.py
"""
import sys
sys.path.insert(0, ".")

from speech.recorder import record_to_file
from speech.asr import transcribe
from speech.tts import speak, play_audio
from agents.graph import build_graph

# Step 1: Record
audio_path = record_to_file()

# Step 2: Transcribe
print("\n📝 Transcribing...")
text = transcribe(audio_path)
print(f"   You said: \"{text}\"")

# Step 3: Run through LangGraph
print("\n🤖 Running through agents...")
graph = build_graph()
result = graph.invoke({
    "user_query":   text,
    "intent":       {},
    "plan":         {},
    "rag_results":  [],
    "web_results":  [],
    "final_answer": "",
    "citations":    [],
    "safety_flags": [],
})

print(f"\n💬 Answer: {result['final_answer']}")
print(f"📚 Citations: {result['citations']}")

# Step 4: Speak the answer
print("\n🔊 Playing response...")
audio_path = speak(result["final_answer"])
play_audio(audio_path)
