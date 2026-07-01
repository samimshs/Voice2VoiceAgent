"""
Phase 4, Task 4.2 — Shared state passed between all agents in the LangGraph graph.
Every agent reads from this state and writes its output back into it.
"""
from typing import TypedDict, List


class AgentState(TypedDict):
    user_query: str          # Raw text from ASR
    intent: dict             # Extracted: budget, material, category, brand, safety_flags
    plan: dict               # Which tools to call and why
    rag_results: List[dict]  # Results from rag.search (private catalog)
    web_results: List[dict]  # Results from web.search (live prices)
    final_answer: str        # Synthesized spoken recommendation
    citations: List[dict]    # doc_ids (private) + URLs (live)
    safety_flags: List[str]  # Detected unsafe topics
