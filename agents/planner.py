"""
Phase 4, Task 4.4 — Planner.

Decides which tools to call based on the intent. No LLM needed here —
pure rule-based logic keeps this fast and predictable.

Rule: if the query asks for live data (current price, availability),
      use both rag.search AND web.search.
      Otherwise, private catalog only.
"""
import json
import logging
from agents.state import AgentState

logging.basicConfig(
    filename="logs/graph.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

LIVE_KEYWORDS = [
    "current price", "available now", "latest", "today",
    "in stock", "right now", "cheapest right now", "live price",
]


def planner_node(state: AgentState) -> dict:
    query  = state["user_query"].lower()
    intent = state["intent"]

    use_web = any(kw in query for kw in LIVE_KEYWORDS)

    plan = {
        "tools":  ["rag.search"] + (["web.search"] if use_web else []),
        "reason": "Live data requested" if use_web else "Private catalog sufficient",
        "filters": {
            "max_price": intent.get("budget"),
            "category":  intent.get("category"),
        },
    }

    logging.info(f"PLANNER | plan={json.dumps(plan)}")
    return {"plan": plan}
