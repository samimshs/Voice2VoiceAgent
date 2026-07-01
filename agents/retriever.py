"""
Phase 4, Task 4.5 — Retriever.

Executes the plan: calls rag.search and optionally web.search,
then stores results in state for the Answerer to use.
"""
import logging
from agents.state import AgentState
from mcp_server.server import rag_search, web_search

logging.basicConfig(
    filename="logs/graph.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)


def retriever_node(state: AgentState) -> dict:
    plan    = state["plan"]
    query   = state["user_query"]
    filters = plan.get("filters", {})

    rag_results = []
    web_results = []

    if "rag.search" in plan["tools"]:
        rag_results = rag_search(
            query=query,
            max_price=filters.get("max_price"),
            category=filters.get("category"),
            top_k=5,
        )
        logging.info(f"RETRIEVER | rag returned {len(rag_results)} results")

    if "web.search" in plan["tools"]:
        web_results = web_search(query=query, top_k=3)
        logging.info(f"RETRIEVER | web returned {len(web_results)} results")

    return {
        "rag_results": rag_results,
        "web_results": web_results,
    }
