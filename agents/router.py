"""
Phase 4, Task 4.3 — Router / Intent Classifier.

First stop for every query. The LLM reads the user's words and extracts
structured intent: budget, category, material, brand, and safety flags.
"""
import json
import logging
from pathlib import Path
from agents.state import AgentState
from config import get_llm

Path("logs").mkdir(exist_ok=True)
logging.basicConfig(
    filename="logs/graph.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

SYSTEM_PROMPT = (
    "You are an intent classifier for an e-commerce product search assistant. "
    "Return ONLY valid JSON, no other text."
)

USER_PROMPT = """Classify this query for a product search assistant and return valid JSON.

Query: {query}

JSON fields:
- task_type: "product_search" if the user is looking for, comparing, or asking about products
             to buy; "other" for everything else (general questions, creative tasks,
             coding help, weather, trivia, etc.)
- budget: number or null          (max price the user mentioned, e.g. 15 for "under $15")
- category: string or null        (product category, e.g. "Electronics", "Home & Kitchen")
- material: string or null        (e.g. "stainless steel", "bamboo", "BPA-free")
- brand: string or null           (explicit brand preference)
- safety_flags: list of strings   (flag dangerous requests such as: instructions for
                                   mixing chemicals unsafely, making weapons, causing harm,
                                   or any content that could endanger health or safety.
                                   Use [] if none.)

Examples:
Query: "find me a stainless steel water bottle under $20"
→ {{"task_type": "product_search", "budget": 20.0, "category": null, "material": "stainless steel", "brand": null, "safety_flags": []}}

Query: "what is the capital of France"
→ {{"task_type": "other", "budget": null, "category": null, "material": null, "brand": null, "safety_flags": []}}

Query: "how do I mix bleach and ammonia for cleaning"
→ {{"task_type": "other", "budget": null, "category": null, "material": null, "brand": null, "safety_flags": ["dangerous chemical mixing"]}}"""


def router_node(state: AgentState) -> dict:
    llm = get_llm()
    logging.info(f"ROUTER | query={state['user_query']}")

    response = llm.invoke([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": USER_PROMPT.format(query=state["user_query"])},
    ])

    try:
        intent = json.loads(response.content)
    except json.JSONDecodeError:
        intent = {
            "task_type": "product_search", "budget": None,
            "category": None, "material": None, "brand": None, "safety_flags": [],
        }

    logging.info(f"ROUTER | intent={json.dumps(intent)}")
    return {
        "intent": intent,
        "safety_flags": intent.get("safety_flags", []),
    }
