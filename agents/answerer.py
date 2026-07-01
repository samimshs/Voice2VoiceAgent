"""
Phase 4, Task 4.6 — Answerer / Critic.

Two-step process:
  1. LLM writes a spoken recommendation from retrieved products only.
  2. Critic pass: verify the answer doesn't hallucinate products.
     If it fails, re-prompt once with stricter instructions.
"""
import json
import logging
from agents.state import AgentState
from config import get_llm

logging.basicConfig(
    filename="logs/graph.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

ANSWER_PROMPT = """You are a voice-based product assistant.
Write a spoken recommendation (≤15 seconds when read aloud, about 50-70 words).
Use ONLY the products listed below. Mention the top pick's name, price, and rating.
Do not invent or mention any product not in the list.

User query: {query}

Available products:
{products}

Return JSON with:
- answer: string (the spoken recommendation)
- citations: list of objects, each with: "doc_id", "title", "price"
"""

CRITIC_PROMPT = """Does this answer use ONLY products from the list?
If yes: {{"grounded": true}}
If it invents facts or products not in the list: {{"grounded": false, "issue": "describe what was invented"}}

Answer: {answer}
Product list: {products}"""


def answerer_node(state: AgentState) -> dict:
    llm = get_llm()
    all_products = (state.get("rag_results") or []) + (state.get("web_results") or [])

    if not all_products:
        return {
            "final_answer": "I couldn't find any products matching your request in our catalog.",
            "citations":    [],
        }

    products_text = json.dumps(all_products[:5], indent=2)

    # Step 1 — Generate answer
    response = llm.invoke([
        {"role": "system", "content": "You are a product assistant. Return only valid JSON."},
        {"role": "user",   "content": ANSWER_PROMPT.format(
            query=state["user_query"], products=products_text,
        )},
    ])

    try:
        result = json.loads(response.content)
    except json.JSONDecodeError:
        result = {"answer": response.content, "citations": []}

    answer    = result.get("answer", "")
    citations = result.get("citations", [])

    # Step 2 — Critic pass
    critic_response = llm.invoke([
        {"role": "system", "content": "You verify answer grounding. Return only valid JSON."},
        {"role": "user",   "content": CRITIC_PROMPT.format(
            answer=answer, products=products_text,
        )},
    ])

    try:
        critic = json.loads(critic_response.content)
    except json.JSONDecodeError:
        critic = {"grounded": True}

    if not critic.get("grounded", True):
        logging.warning(f"ANSWERER | grounding failed: {critic.get('issue')}")
        retry = llm.invoke([
            {"role": "system", "content": "Strict mode: only use exact products listed. Return valid JSON."},
            {"role": "user",   "content": ANSWER_PROMPT.format(
                query=state["user_query"], products=products_text,
            )},
        ])
        try:
            result    = json.loads(retry.content)
            answer    = result.get("answer", answer)
            citations = result.get("citations", citations)
        except json.JSONDecodeError:
            pass

    logging.info(f"ANSWERER | answer={answer[:100]}")
    return {
        "final_answer": answer,
        "citations":    citations,
    }
